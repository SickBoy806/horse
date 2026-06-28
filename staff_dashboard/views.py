from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def staff_dashboard(request, branch):
    if not request.user.branch or request.user.branch.name.lower() != branch.lower():
        return render(request, 'errors/unauthorized.html', status=403)

    context = {
        'branch': request.user.branch.name.title(),
    }
    return render(request, 'staff_dashboard/dashboard.html', context)