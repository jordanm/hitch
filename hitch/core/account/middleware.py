from django.conf import settings
from django.http import HttpResponseRedirect

from hitch.core.account.models import Account, decode_plogin_cookie

PLOGIN_COOKIE_NAME = settings.PLOGIN_COOKIE_NAME

class AuthenticationMiddleware(object):
    def process_request(self, request):
        request.account = None
        print request.session.get('__accountid__')
        try:
            account = Account.objects.get(id=request.session['__accountid__'])
        except (Account.DoesNotExist, KeyError):
            pass
        else:
            account.attach(request)
            return
        
        cookie = request.COOKIES.get(PLOGIN_COOKIE_NAME)
        if cookie:
            try:
                email, token = decode_plogin_cookie(cookie)
            except ValueError:
                pass
            else:
                account = Account.objects.authenticate(email=email, token=token)
                if account:
                    account.login(request)
                    response = HttpResponseRedirect(request.get_full_path())
                    account.persist_login(response)
                    return response