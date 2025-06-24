from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def staff_dashboard(request, branch):
    if request.user.branch.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    context = {
        'branch': request.user.branch.title(),
    }
    return render(request, 'staff_dashboard/dashboard.html', context)