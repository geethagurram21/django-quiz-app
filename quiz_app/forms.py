from django import forms
from django.contrib.auth.models import User
from .models import Module
class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['username', 'email']
    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password2'):
            raise forms.ValidationError("Passwords don't match")
        return cleaned
class QuizSelectForm(forms.Form):
    modules = forms.ModelMultipleChoiceField(queryset=Module.objects.all(), widget=forms.CheckboxSelectMultiple, required=True)
