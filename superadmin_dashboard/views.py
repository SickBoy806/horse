from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def superadmin_dashboard(request):
    context = {
        'branch': request.user.branch.title(),
    }
    return render(request, 'superadmin_dashboard/dashboard.html', context)