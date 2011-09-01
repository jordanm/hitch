import logging
from cStringIO import StringIO
from datetime import datetime, timedelta
from mimetypes import guess_type

from django.conf import settings
from django.db import models
from django.http import HttpResponse

from hitch.support.models import BinaryField, CharField, Manager, Model, UniqueIdentifierField

log = logging.getLogger(__name__)

class FileManager(Manager):
    def prune(self):
        self.filter(expiry__isnull=False, expiry__lte=datetime.now()).delete()
        
    def store(self, filename, data, expiry=None, mimetype=''):
        if isinstance(expiry, timedelta):
            expiry = datetime.now() + expiry
        if not mimetype:
            mimetype, encoding = guess_type(filename, False)
        return self.create(filename=filename, mimetype=(mimetype or ''),
            expiry=expiry, size=len(data), data=data)
        
    def upload(self, upload, expiry=None, mimetype=''):
        return self.store(upload.name, ''.join(upload.chunks()), expiry, mimetype)

class File(Model):
    class Meta:
        app_label = 'core'
        
    id = UniqueIdentifierField()
    filename = CharField('Filename')
    mimetype = CharField('Mimetype', default='', blank=True)
    size = models.IntegerField('Size', default=0)
    occurrence = models.DateTimeField('Occurrence', default=datetime.now)
    expiry = models.DateTimeField('Expiry', null=True, blank=True)
    data = BinaryField()
    objects = FileManager()
    
    def __unicode__(self):
        return self.id
    
    def construct_response(self, download=True, filename=None, mimetype=None):
        response = HttpResponse(str(self.data), mimetype or self.mimetype)
        if download:
            response['Content-Disposition'] = 'attachment; filename=%s' % (filename or self.filename)
        return response
    
    def open(self):
        return StringIO(self.data)