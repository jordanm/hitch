from django import forms
from django.conf import settings

from hitch.support.forms import Form

class CreateAccountForm(Form):
    fullname = forms.CharField(label='Full name', max_length=60)
    email = forms.EmailField(label='Email address', max_length=180)
    password = forms.CharField(label='Password', min_length=8, 
        widget=forms.PasswordInput(render_value=False))

class LoginForm(Form):
    metadata = {
        'fields': {
            'password': {
                'action': {'id': 'reset-password-action', 'text': 'Forget your password?'}
            }
        }
    }
    
    email = forms.EmailField(label='E-mail address', max_length=180)
    password = forms.CharField(label='Password', widget=forms.PasswordInput(render_value=False))
    persistent = forms.BooleanField(label='Remember me', required=False)
    next = forms.CharField(required=False, widget=forms.HiddenInput)