from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Count
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from accounts.models import CustomUser
from core.models import Task, SupportTicket, Branch, SystemLog, Notification
from veterinarian_dashboard.models import Animal
from user_dashboard.models import DailyActivityReport
from .forms import BranchForm, CustomUserForm
from datetime import date


def is_superadmin(user):
    return user.is_authenticated and user.role == 'superadmin'


@login_required
def superadmin_dashboard(request):
    if request.user.role != 'superadmin':
        return render(request, 'errors/unauthorized.html', status=403)

    total_users = CustomUser.objects.exclude(role='superadmin').count()
    total_animals = Animal.objects.count()
    total_branches = CustomUser.objects.values('branch').distinct().count()
    reports_today = DailyActivityReport.objects.filter(date=timezone.now().date()).count()

    all_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    notifications = all_notifications[:5]
    unread_notifications_count = all_notifications.filter(is_read=False).count()

    role_data = CustomUser.objects.values('role').exclude(role='superadmin').annotate(count=Count('id'))
    role_labels = [entry['role'].capitalize() for entry in role_data]
    role_counts = [entry['count'] for entry in role_data]

    task_status_data = [
        Task.objects.filter(status='pending').count(),
        Task.objects.filter(status='in_progress').count(),
        Task.objects.filter(status='completed').count(),
    ]

    branch_names = CustomUser.objects.values_list('branch', flat=True).distinct()
    branch_summaries = []
    for branch_name in branch_names:
        branch_obj = Branch.objects.filter(name=branch_name).first()
        if not branch_obj:
            continue

        summary = {
            'branch': branch_name,
            'user_count': CustomUser.objects.filter(branch=branch_name).exclude(role='superadmin').count(),
            'task_count': Task.objects.filter(branch=branch_obj).count(),
            'reports_today': DailyActivityReport.objects.filter(branch=branch_obj, date=timezone.now().date()).count(),
            'animal_count': Animal.objects.filter(branch=branch_obj).count()
        }
        branch_summaries.append(summary)

    context = {
        'total_users': total_users,
        'total_animals': total_animals,
        'total_branches': total_branches,
        'reports_today': reports_today,
        'role_labels': role_labels,
        'role_counts': role_counts,
        'task_status_data': task_status_data,
        'branch_summaries': branch_summaries,
        'notifications': notifications,
        'unread_notifications_count': unread_notifications_count,
    }

    return render(request, 'superadmin_dashboard/dashboard.html', context)


@login_required
def superadmin_manage_branches(request):
    if not is_superadmin(request.user):
        return render(request, 'errors/unauthorized.html', status=403)

    branches = Branch.objects.all().order_by('name')
    return render(request, 'superadmin_dashboard/manage_branches.html', {'branches': branches})


@login_required
def superadmin_manage_users(request):
    if not is_superadmin(request.user):
        return render(request, 'errors/unauthorized.html', status=403)

    users = CustomUser.objects.all().order_by('branch', 'role', 'username')
    return render(request, 'superadmin_dashboard/user_list.html', {'users': users})


@login_required
def superadmin_user_add(request):
    if not is_superadmin(request.user):
        return render(request, 'errors/unauthorized.html', status=403)

    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data['password']:
                user.password = make_password(form.cleaned_data['password'])
            user.save()
            return redirect('superadmin_manage_users')
    else:
        form = CustomUserForm()

    return render(request, 'superadmin_dashboard/user_form.html', {'form': form, 'title': 'Add User'})


@login_required
def superadmin_user_edit(request, user_id):
    if not is_superadmin(request.user):
        return render(request, 'errors/unauthorized.html', status=403)

    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = CustomUserForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data['password']:
                user.password = make_password(form.cleaned_data['password'])
            user.save()
            return redirect('superadmin_manage_users')
    else:
        form = CustomUserForm(instance=user)

    return render(request, 'superadmin_dashboard/user_form.html', {'form': form, 'title': 'Edit User'})


@login_required
def superadmin_user_delete(request, user_id):
    if not is_superadmin(request.user):
        return render(request, 'errors/unauthorized.html', status=403)

    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('superadmin_manage_users')

    return render(request, 'superadmin_dashboard/user_confirm_delete.html', {'user': user})


@login_required
def superadmin_analytics(request):
    if not is_superadmin(request.user):
        return render(request, 'errors/unauthorized.html', status=403)

    role_data = CustomUser.objects.values('role').annotate(count=Count('id'))
    role_labels = [r['role'].capitalize() for r in role_data]
    role_counts = [r['count'] for r in role_data]

    task_status_qs = Task.objects.values('status').annotate(count=Count('id'))
    task_status_map = {'Pending': 0, 'In Progress': 0, 'Completed': 0}
    for entry in task_status_qs:
        label = entry['status'].replace('_', ' ').title()
        if label in task_status_map:
            task_status_map[label] = entry['count']

    today = timezone.now().date()
    reports_today = DailyActivityReport.objects.filter(date=today).count()

    branch_summaries = []
    all_branches = Branch.objects.filter(is_active=True)
    for branch in all_branches:
        user_count = CustomUser.objects.filter(branch=branch.name).count()
        task_count = Task.objects.filter(branch=branch).count()
        reports = DailyActivityReport.objects.filter(branch=branch, date=today).count()
        animals = Animal.objects.filter(branch=branch, is_active=True).count()

        branch_summaries.append({
            'branch': branch.name,
            'user_count': user_count,
            'task_count': task_count,
            'reports_today': reports,
            'animal_count': animals
        })

    top_users = (
        DailyActivityReport.objects
        .values('user__first_name', 'user__branch')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    return render(request, 'superadmin_dashboard/analytics.html', {
        'role_labels': role_labels,
        'role_counts': role_counts,
        'task_status_data': list(task_status_map.values()),
        'reports_today': reports_today,
        'branch_summaries': branch_summaries,
        'top_users': top_users,
    })


@login_required
def superadmin_tickets(request):
    if not is_superadmin(request.user):
        return render(request, 'errors/unauthorized.html', status=403)

    tickets = SupportTicket.objects.select_related('created_by').order_by('-created_at')
    branch_groups = {}
    for ticket in tickets:
        branch_name = ticket.branch.name if ticket.branch else "Unknown"
        if branch_name not in branch_groups:
            branch_groups[branch_name] = []
        branch_groups[branch_name].append(ticket)

    return render(request, 'superadmin_dashboard/tickets.html', {'branch_groups': branch_groups})


@login_required
@user_passes_test(is_superadmin)
def manage_branches(request):
    branches = Branch.objects.all().order_by('name')
    return render(request, 'superadmin_dashboard/manage_branches.html', {'branches': branches})


@login_required
@user_passes_test(is_superadmin)
def add_branch(request):
    form = BranchForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('superadmin_manage_branches')
    return render(request, 'superadmin_dashboard/branch_form.html', {'form': form, 'title': 'Add Branch'})


@login_required
@user_passes_test(is_superadmin)
def edit_branch(request, branch_id):
    branch = get_object_or_404(Branch, id=branch_id)
    form = BranchForm(request.POST or None, instance=branch)
    if form.is_valid():
        form.save()
        return redirect('superadmin_manage_branches')
    return render(request, 'superadmin_dashboard/branch_form.html', {'form': form, 'title': 'Edit Branch'})


@login_required
@user_passes_test(is_superadmin)
def delete_branch(request, branch_id):
    branch = get_object_or_404(Branch, id=branch_id)
    if request.method == 'POST':
        branch.delete()
        return redirect('superadmin_manage_branches')
    return render(request, 'superadmin_dashboard/branch_confirm_delete.html', {'branch': branch})


@login_required
def superadmin_view_logs(request):
    if not is_superadmin(request.user):
        return render(request, 'errors/unauthorized.html', status=403)

    logs = SystemLog.objects.all().order_by('-timestamp')[:200]
    return render(request, 'superadmin_dashboard/system_logs.html', {'logs': logs})


@login_required
def superadmin_permissions(request):
    if not request.user.is_authenticated or request.user.role != 'superadmin':
        return render(request, 'errors/unauthorized.html', status=403)

    branch_filter = request.GET.get("branch")
    role_filter = request.GET.get("role")
    status_filter = request.GET.get("status")

    users = CustomUser.objects.exclude(id=request.user.id)

    if branch_filter:
        users = users.filter(branch=branch_filter)
    if role_filter:
        users = users.filter(role=role_filter)
    if status_filter == 'locked':
        users = users.filter(is_active=False)
    elif status_filter == 'active':
        users = users.filter(is_active=True)

    return render(request, 'superadmin_dashboard/permissions.html', {
        'users': users,
        'branches': CustomUser.objects.values_list('branch', flat=True).distinct(),
        'branch_filter': branch_filter,
        'role_filter': role_filter,
        'status_filter': status_filter,
    })


@login_required
@user_passes_test(is_superadmin)
def promote_to_vet(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if user.role != 'veterinarian':
        user.role = 'veterinarian'
        user.save()
        messages.success(request, f"{user.get_full_name()} promoted to Veterinarian.")
    return redirect('superadmin_permissions')


@login_required
@user_passes_test(is_superadmin)
def lock_account(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if user.is_active:
        user.is_active = False
        user.save()
        messages.success(request, f"{user.get_full_name()}'s account has been locked.")
    return redirect('superadmin_permissions')


@login_required
@user_passes_test(is_superadmin)
def unlock_account(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if not user.is_active:
        user.is_active = True
        user.save()
        messages.success(request, f"{user.get_full_name()}'s account has been unlocked.")
    return redirect('superadmin_permissions')
