from django import forms
from accounts.models import CustomUser
from core.models import VetTask, MedicalRecord, SupportTicket, TicketReply


class CustomUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'role', 'branch', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])  # hash the password
        if commit:
            user.save()
        return user


class AssignTaskForm(forms.ModelForm):
    class Meta:
        model = VetTask
        fields = ['title', 'description', 'animal', 'assigned_to', 'priority', 'due_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        branch = kwargs.pop('branch', None)
        super().__init__(*args, **kwargs)
        if branch:
            self.fields['assigned_to'].queryset = CustomUser.objects.filter(
                branch=branch, 
                role__in=['user', 'veterinarian', 'staff']
            )


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ['animal', 'report_type', 'diagnosis', 'treatment', 'document']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 3}),
            'treatment': forms.Textarea(attrs={'rows': 3}),
        }


class VetTaskForm(forms.ModelForm):
    class Meta:
        model = VetTask
        fields = ['title', 'description', 'animal', 'assigned_to', 'priority', 'due_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        branch = kwargs.pop('branch', None)
        super().__init__(*args, **kwargs)
        if branch:
            self.fields['assigned_to'].queryset = CustomUser.objects.filter(
                branch=branch, 
                role__in=['user', 'veterinarian', 'staff']
            )


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['subject', 'description', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class TicketReplyForm(forms.ModelForm):
    class Meta:
        model = TicketReply
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3}),
        }
