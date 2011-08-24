import logging

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from jinja2 import contextfunction

from hitch.core.account import forms
from hitch.core.account.models import Account
from hitch.core.views import Views
from hitch.support.views import viewable

log = logging.getLogger(__name__)

class AccountViews(Views):
    @viewable('account-create', r'^account/create', secured=True)
    def create(self, request, response):
        if request.account:
            return response.ignore()
        
        if request.posting:
            form = forms.CreateAccountForm(data=request.POST)
            if form.is_valid():
                try:
                    account = Account.objects.create_and_login(request, form.cleaned_data)
                except Exception:
                    log.exception('unhandled exception during account creation')
                    response.message('An unknown error has occurred.', 'error')
                    if request.is_ajax():
                        return response.error().json()
                else:
                    url = '/'
                    if request.is_ajax():
                        return response.json(url=url)
                    else:
                        return response.redirect(url)
            elif request.is_ajax():
                return response.collect(form).error('invalid-submission').json()
        else:
            form = forms.CreateAccountForm()
            
        if request.is_ajax():
            return response.render('account/modal-create-account.html', form=form)
        else:
            return response.render('account/create-account.html', form=form)

    @viewable('account-login', r'^login', secured=True)
    def login(self, request, response):
        target = request.GET.get('next')
        if not target or '//' in target or ' ' in target:
            target = '/'
        if request.account:
            if request.is_ajax():
                return response.json()
            else:
                return response.redirect(target)
        
        if request.posting:
            form = forms.LoginForm(data=request.POST)
            if form.is_valid():
                account = Account.objects.authenticate(email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'])
                if account:
                    if account.status == 'active':
                        account.login(request)
                        if form.cleaned_data['persistent']:
                            account.persist_login(response)
                        if request.is_ajax():
                            return response.json(url=target)
                        else:
                            return response.redirect(target)
                    else:
                        response.message('Your account is currently inactive.', 'error')
                        if request.is_ajax():
                            return response.error('inactive-account').json()
                else:
                    response.message('Invalid account or password.', 'error')
                    if request.is_ajax():
                        return response.error('invalid-account').json()
            elif request.is_ajax():
                return response.error('invalid-credentials').json()
        else:
            form = forms.LoginForm()
            
        if request.is_ajax():
            pass
        else:
            return response.render('account/login.html', form=form, target=target)