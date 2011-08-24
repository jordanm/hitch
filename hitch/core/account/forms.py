from django import forms
from django.conf import settings

class CreateAccountForm(forms.Form):
    fullname = forms.CharField(label='Full name', max_length=60)
    email = forms.EmailField(label='Email address', max_length=180)
    password = forms.CharField(label='Password', widget=forms.PasswordInput(render_value=False))

class LoginForm(forms.Form):
    email = forms.EmailField(label='E-mail address', max_length=180)
    password = forms.CharField(label='Password', widget=forms.PasswordInput(render_value=False))
    persistent = forms.BooleanField(label='Remember me', required=False)
    redirect = forms.CharField(required=False, widget=forms.HiddenInput)