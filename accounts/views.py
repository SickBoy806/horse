from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import CustomUserCreationForm

# 🔐 User Login View
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            role = user.role

            if role == 'superadmin':
                return redirect('superadmin_dashboard')

            if not user.branch:
                messages.error(request, "Your account has no branch assigned. Contact an administrator.")
                logout(request)
                return redirect('login')

            branch = user.branch.name.lower()

            if role == 'admin':
                return redirect(f'/dashboard/admin/{branch}/')
            elif role == 'veterinarian':
                return redirect(f'/dashboard/vet/{branch}/')
            elif role == 'staff':
                return redirect(f'/dashboard/staff/{branch}/')
            elif role == 'user':
                return redirect(f'/dashboard/user/{branch}/')
        else:
            messages.error(request, "Unauthorized user. Please try again.")
            return redirect('login')

    return render(request, 'accounts/login.html')

# 🚪 Logout View
def user_logout(request):
    logout(request)
    return redirect('login')

# 👤 Create New User (Admin / SuperAdmin Only)
@login_required
def create_user_view(request):
    if request.user.role not in ['superadmin', 'admin']:
        return render(request, 'errors/unauthorized.html', status=403)

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully.")
            branch_name = request.user.branch.name.lower() if request.user.branch else ''
            return redirect('superadmin_dashboard' if request.user.role == 'superadmin' else f'/dashboard/admin/{branch_name}/')
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/create_user.html', {'form': form})