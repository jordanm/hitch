import base64
import logging
import random
from datetime import datetime
from hashlib import sha1

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.db import models
from django.db.transaction import commit_on_success

from hitch.support.models import CharField, EmailField, Manager, Model, UniqueIdentifierField
from hitch.support.util import choices, uniqid

log = logging.getLogger(__name__)

PLOGIN_COOKIE_MAXAGE = settings.PLOGIN_COOKIE_MAXAGE
PLOGIN_COOKIE_NAME = settings.PLOGIN_COOKIE_NAME

def decode_plogin_cookie(value):
    return base64.b64decode(value).split('|')

def encode_plogin_cookie(email, token):
    return base64.b64encode('%s|%s' % (email, token))

class AccountManager(Manager):
    def acquire(self, email):
        try:
            return self.get(email=email.strip().lower())
        except (Account.DoesNotExist, AttributeError):
            return None
        
    def authenticate(self, **credentials):
        facebookid = credentials.get('facebookid')
        if facebookid:
            try:
                return self.get(facebookid=facebookid)
            except Account.DoesNotExist:
                return None
            
        email = credentials.get('email')
        if not email:
            return None
        
        email = email.strip().lower()
        try:
            account = self.get(email=email)
        except Account.DoesNotExist:
            return None
        
        password = credentials.get('password')
        if password and account.check_password(password):
            return account

    @commit_on_success
    def create(self, **params):
        account = Account(
            status=params.get('status', 'active'),
            email=params['email'].strip().lower(),
            fullname=params.get('fullname') or '',
            phone_number=params.get('phone_number') or '',
            facebookid=params.get('facebookid') or None,
            facebook_username=params.get('facebook_username') or None,
            superuser=params.get('superuser', False),
        )
        
        hashed_password = params.get('hashed_password')
        if hashed_password:
            account.password = hashed_password
            
        password = params.get('password')
        if password:
            account.set_password(password)
            
        account.full_clean()
        account.save(force_insert=True)
        
        if account.superuser:
            account.grant_superuser()
        return account
    
    def create_and_login(self, request, data, authentication='internal'):
        identity = '%s (%s)' % (data['fullname'], data['email'].strip().lower())
        log.info('attempting to create account for %s', identity)
        
        try:
            account = self.create(**data)
        except Exception:
            log.exception('account creation failed for %s', identity)
            raise
        
        log.info('created account for %s', identity)
        if not authentication:
            return account
        
        try:
            account.login(request, authentication)
        except Exception:
            log.exception('account authentication failed for %s', account)
            raise
        else:
            return account

class Account(Model):
    """An account."""
    
    class Meta:
        app_label = 'core'
        
    StatusTokens = ('active', 'inactive')
    
    id = UniqueIdentifierField()
    status = CharField('Status', choices=choices(StatusTokens), default='active')
    email = EmailField('Email', unique=True)
    password = CharField('Password', blank=True)
    fullname = CharField('Full name', blank=True)
    phone_number = CharField('Phone number', blank=True)
    facebookid = CharField('Facebook id', unique=True, null=True, blank=True, default=None)
    facebook_username = CharField('Facebook username', unique=True, null=True, blank=True, default=None)
    superuser = models.BooleanField('Superuser', default=False)
    date_joined = models.DateTimeField('Date joined', default=datetime.now)
    last_login = models.DateTimeField('Last login', default=datetime.now)
    objects = AccountManager()
    
    def __unicode__(self):
        return (self.fullname or self.email or self.id)
    
    @property
    def firstname(self):
        fullname = self.fullname
        return (fullname.partition(' ')[0] if ' ' in fullname else fullname)

    @property
    def lastname(self):
        return (self.fullname.partition(' ')[2] if ' ' in self.fullname else '')

    def attach(self, request):
        request.account = self
        if self.superuser:
            try:
                request.user = User.objects.get(email=self.email)
            except User.DoesNotExist:
                request.user = AnonymousUser()
        
    def check_password(self, password):
        correct_password = self.password
        if correct_password:
            try:
                algorithm, salt, hash = self.password.split('$')
            except ValueError:
                return False
            return self._generate_hexdigest(algorithm, salt, password) == hash
        else:
            return False
    
    def grant_superuser(self):
        if not self.superuser:
            self.update(superuser=True)
        try:
            User.objects.get(email=self.email)
        except User.DoesNotExist:
            User(username=uniqid()[:30], first_name=self.firstname, last_name=self.lastname,
                email=self.email, is_staff=True, is_superuser=True).save()
    
    def login(self, request, authentication='internal'):
        session = request.session
        if '__accountid__' in request.session:
            if session['__accountid__'] != self.id:
                session.flush()
        else:
            session.cycle_key()
            
        session['__accountid__'] = self.id
        session['authentication-method'] = authentication
        self.attach(request)
        self.update(last_login=datetime.now())

    def logout(self, request):
        request.session.flush()
        request.account = None

    def persist_login(self, response):
        login = PersistentLogin(account=self, token=uniqid())
        login.save()
        
        value = encode_plogin_cookie(self.email, login.token)
        response.set_cookie(PLOGIN_COOKIE_NAME, value, PLOGIN_COOKIE_MAXAGE)

    def revoke_superuser(self):
        if self.superuser:
            self.update(superuser=False)
        try:
            User.objects.get(email=self.email).delete()
        except User.DoesNotExist:
            pass
    
    def set_password(self, password, algorithm='sha1'):
        salt = base64.b64encode(str(u'%0x' % random.getrandbits(37)))[:6]
        self.password = '%s$%s$%s' % (algorithm, salt,
            self._generate_hexdigest(algorithm, salt, password))
        
    def _generate_hexdigest(self, algorithm, salt, password):
        if algorithm == 'sha1':
            return sha1((salt + password).encode('utf-8')).hexdigest()
        else:
            raise ValueError('unknown algorithm')
        
class PasswordReset(Model):
    class Meta:
        app_label = 'core'
        
    token = CharField('Token', primary_key=True)
    account = models.ForeignKey(Account)
    
    def __unicode__(self):
        return self.token
    
    def reset(self, password):
        self.account.set_password(password)
        self.account.save()
        self.delete()

class PersistentLogin(Model):
    class Meta:
        app_label = 'core'
        
    token = CharField('Token', primary_key=True)
    account = models.ForeignKey(Account)
    
    def __unicode__(self):
        return self.token
    
    @classmethod
    def purge(cls, account, token):
        try:
            cls.objects.get(account=account, token=token).delete()
        except cls.DoesNotExist:
            pass