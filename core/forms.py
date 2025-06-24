from django import forms
from .models import Task
from accounts.models import CustomUser

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'due_date']

    def _init_(self, *args, **kwargs):
        user = kwargs.pop('user')
        super()._init_(*args, **kwargs)
        # Filter users from same branch and role staff/user
        self.fields['assigned_to'].queryset = CustomUser.objects.filter(
            branch=user.branch, role__in=['staff', 'user']
        )