from collections import deque

from django import forms
from django.core import validators
from django.db import models, transaction

from hitch.support.util import uniqid

class Manager(models.Manager):
    def create(self, clean=False, **params):
        instance = self.model(**params)
        if clean:
            instance.full_clean()
        instance.save(force_insert=True)
        return instance
    
    def create_with_mapping(self, data, clean=False, exclusions=None, exclude_pk=True, m2m=True, **params):
        mapping = self._collate_values(self._enumerate_fields(exclusions, exclude_pk), params, data)
        instance = self.create(clean=clean, **mapping)
        if m2m:
            self._save_m2m(instance, params, data)
        return instance
    
    def update_with_mapping(self, instance, data, clean=False, exclusions=None, m2m=True, **params):
        mapping = self._collate_values(self._enumerate_fields(exclusions), params, data)
        for field, value in mapping.iteritems():
            setattr(instance, field, value)
        if clean:
            instance.full_clean()
        self.filter(pk=instance.pk).update(**mapping)
        if m2m:
            self._save_m2m(instance, params, data)
        return instance
    
    def _collate_values(self, fields, *sources):
        values = {}
        for field in fields:
            for source in sources:
                if source and field in source:
                    values[field] = source[field]
                    break
        else:
            return values
        
    def _enumerate_fields(self, exclusions=None, exclude_pk=True):
        fields = set([field.name for field in self.model._meta.local_fields])
        if exclude_pk:
            fields.remove(self.model._meta.pk.name)
        if exclusions:
            fields.difference_update(exclusions)
        return fields
    
    def _save_m2m(self, instance, *sources):
        for field in self.model._meta.many_to_many:
            name = field.name
            for source in sources:
                if name in source:
                    field.save_form_data(instance, source[name])
                    break
                
class Model(models.Model):
    class Meta:
        abstract = True
    
    def update(self, data=None, clean=False, **params):
        return type(self).objects.update_with_mapping(self, data, clean=clean, **params)

class BinaryField(models.Field):
    def db_type(self):
        return 'bytea'
    
    def formfield(self, **params):
        raise TypeError('Binary field should not be exposed via a form.')
    
    def get_prep_value(self, value):
        return buffer(value)

class CharField(models.TextField):
    def formfield(self, **params):
        return models.Field.formfield(self, **params)

    def get_prep_value(self, value):
        value = super(CharField, self).get_prep_value(value)
        return (None if self.null and not value else value)

class EmailField(CharField):
    default_validators = [validators.validate_email]
    description = 'E-mail address'
    
    def formfield(self, **params):
        defaults = {'form_class': forms.EmailField}
        defaults.update(params)
        return super(EmailField, self).formfield(**defaults)

class SlugField(CharField):
    def __init__(self, *args, **params):
        if 'db_index' not in params:
            params['db_index'] = True
        super(SlugField, self).__init__(*args, **params)
        
    def formfield(self, **params):
        defaults = {'form_class': forms.SlugField}
        defaults.update(params)
        return super(SlugField, self).formfield(**defaults)

class UniqueIdentifierField(CharField):
    def __init__(self, name='Identifier', primary_key=True, default=uniqid, **params):
        super(UniqueIdentifierField, self).__init__(name, primary_key=primary_key, default=default, **params)