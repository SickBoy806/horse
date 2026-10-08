"""Stores: feed, medicine and consumable stock."""
import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import CustomUser
from .forms import StockItemForm, StockMovementForm, StockTakeForm
from .models import Branch, StockItem, StockMovement
from .utils import log_action, notify_users

STOCK_MANAGERS = ('admin', 'superadmin', 'staff', 'veterinarian')
SIGN = {'received': 1, 'issued': -1, 'wasted': -1}


def with_on_hand(qs):
    return qs.annotate(stock_on_hand=Coalesce(Sum('movements__quantity'), Value(0),
                                              output_field=DecimalField(max_digits=12, decimal_places=2)))


def _scoped_items(user):
    qs = StockItem.objects.select_related('branch')
    return qs if user.role == 'superadmin' else qs.filter(branch=user.branch)


def record_movement(item, kind, quantity, user, **fields):
    """Create a signed movement and re-check the reorder level. Used by views and the vet record form."""
    movement = StockMovement.objects.create(item=item, kind=kind, quantity=quantity, recorded_by=user, **fields)
    check_level(item)
    return movement


def check_level(item):
    """Notify stock managers once when an item drops to its reorder level; re-arm when restocked."""
    item = StockItem.objects.get(pk=item.pk)  # fresh on_hand
    low = item.on_hand <= item.reorder_level
    if low and not item.low_stock_notified:
        managers = CustomUser.objects.filter(branch=item.branch, role__in=('admin', 'staff'), is_active=True)
        if item.category in StockItem.MEDICAL_CATEGORIES:
            managers = managers | CustomUser.objects.filter(branch=item.branch, role='veterinarian', is_active=True)
        state = 'out of stock' if item.on_hand <= 0 else f'low: {item.on_hand:g} {item.get_unit_display()} left'
        notify_users(users=managers.distinct(), notification_type='system_alert', title=f'Stock alert: {item.name}',
                     message=f"{item.name} is {state} (reorder level {item.reorder_level:g}).",
                     link=f'/core/stock/{item.id}/')
        StockItem.objects.filter(pk=item.pk).update(low_stock_notified=True)
    elif not low and item.low_stock_notified:
        StockItem.objects.filter(pk=item.pk).update(low_stock_notified=False)


@login_required
def stock_list(request):
    user = request.user
    items = with_on_hand(_scoped_items(user))
    f = {k: request.GET.get(k, '').strip() for k in ('q', 'category', 'level', 'show', 'branch')}
    if f['show'] != 'all':
        items = items.filter(is_active=True)
    if f['q']:
        items = items.filter(Q(name__icontains=f['q']) | Q(supplier__icontains=f['q']))
    if f['category']:
        items = items.filter(category=f['category'])
    if f['branch'] and user.role == 'superadmin':
        items = items.filter(branch__name=f['branch'])
    items = list(items.order_by('category', 'name'))
    all_active = [i for i in items if i.is_active]
    stats = {
        'items': len(all_active),
        'low': sum(1 for i in all_active if i.level == 'low'),
        'out': sum(1 for i in all_active if i.level == 'out'),
        'expiring': sum(1 for i in all_active if i.expiring_batches().exists()),
    }
    if f['level'] == 'attention':
        items = [i for i in items if i.level != 'ok' or i.expiring_batches().exists()]
    elif f['level'] in ('low', 'out', 'ok'):
        items = [i for i in items if i.level == f['level']]

    if request.GET.get('export') == 'csv':
        return _csv(items)

    query = request.GET.copy()
    query.pop('export', None)
    return render(request, 'core/stock/list.html', {
        'items': items, 'stats': stats, 'f': f, 'querystring': query.urlencode(),
        'category_choices': StockItem.CATEGORY_CHOICES,
        'branches': Branch.objects.filter(is_active=True).order_by('name') if user.role == 'superadmin' else None,
        'can_manage': user.role in STOCK_MANAGERS,
    })


def _csv(items):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="stock-{timezone.localdate():%Y%m%d}.csv"'
    response.write('﻿')
    w = csv.writer(response)
    w.writerow(['Item', 'Category', 'Branch', 'On hand', 'Unit', 'Reorder level', 'Reorder qty', 'Status',
                'Supplier', 'In use'])
    for i in items:
        w.writerow([i.name, i.get_category_display(), i.branch.name, f'{i.on_hand:g}', i.get_unit_display(),
                    f'{i.reorder_level:g}', f'{i.reorder_quantity:g}' if i.reorder_quantity is not None else '',
                    i.level_label, i.supplier, 'Yes' if i.is_active else 'No'])
    return response


@login_required
def stock_detail(request, item_id):
    user = request.user
    item = get_object_or_404(with_on_hand(_scoped_items(user)), pk=item_id)
    can_manage = user.role in STOCK_MANAGERS
    allowed = ('received', 'issued', 'wasted') if can_manage else ('issued',)

    move_form = StockMovementForm(item=item, allowed_kinds=allowed)
    take_form = StockTakeForm()
    if request.method == 'POST' and item.is_active:
        action = request.POST.get('action')
        if action == 'movement':
            move_form = StockMovementForm(request.POST, item=item, allowed_kinds=allowed)
            if move_form.is_valid():
                data = move_form.cleaned_data
                kind = data['kind']
                with transaction.atomic():
                    record_movement(item, kind, data['quantity'] * SIGN[kind], user,
                                    date=data['date'], animal=data.get('animal'),
                                    batch_number=data.get('batch_number') or '', expiry_date=data.get('expiry_date'),
                                    reference=data.get('reference') or '', notes=data.get('notes') or '')
                log_action(user=user, action='update',
                           message=f"Stock {kind}: {data['quantity']:g} {item.get_unit_display()} {item.name}")
                messages.success(request, f"{dict(StockMovement.KIND_CHOICES)[kind]}: {data['quantity']:g} "
                                          f"{item.get_unit_display()} of {item.name}.")
                return redirect('stock_detail', item_id=item.id)
        elif action == 'stocktake' and can_manage:
            take_form = StockTakeForm(request.POST)
            if take_form.is_valid():
                delta = take_form.cleaned_data['counted'] - item.on_hand
                if delta:
                    record_movement(item, 'adjustment', delta, user, date=timezone.localdate(),
                                    notes=take_form.cleaned_data['notes'] or 'Stock take')
                    log_action(user=user, action='update', message=f"Stock take {item.name}: {delta:+g}")
                    messages.success(request, f"Stock take recorded — adjusted by {delta:+g} {item.get_unit_display()}.")
                else:
                    messages.success(request, 'Stock take matches the system — no adjustment needed.')
                return redirect('stock_detail', item_id=item.id)
        messages.error(request, 'Please correct the errors below.')

    movements = item.movements.select_related('animal', 'recorded_by', 'medical_record')[:100]
    return render(request, 'core/stock/detail.html', {
        'item': item, 'movements': movements, 'batches': item.expiring_batches(),
        'move_form': move_form, 'take_form': take_form, 'can_manage': can_manage,
    })


@login_required
def stock_item_edit(request, item_id=None):
    user = request.user
    if user.role not in STOCK_MANAGERS:
        return render(request, 'errors/unauthorized.html', status=403)
    item = get_object_or_404(_scoped_items(user), pk=item_id) if item_id else StockItem(branch=user.branch)
    if request.method == 'POST':
        form = StockItemForm(request.POST, instance=item, user=user)
        if form.is_valid():
            item = form.save()
            if item_id:  # a changed reorder level may cross the threshold; new items have no stock yet
                check_level(item)
            log_action(user=user, action='update' if item_id else 'create', message=f"Stock item saved: {item.name}")
            messages.success(request, f"{item.name} saved.")
            return redirect('stock_detail', item_id=item.id)
    else:
        form = StockItemForm(instance=item, user=user)
    return render(request, 'core/stock/item_form.html', {'form': form, 'item': item, 'is_new': item_id is None})
