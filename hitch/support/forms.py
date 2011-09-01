from collections import defaultdict
from json import dumps, loads

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Model
from django.forms.forms import BoundField
from django.forms.formsets import BaseFormSet
from django.forms.models import BaseModelFormSet, modelformset_factory
from django.forms.util import ErrorList
from django.forms.widgets import HiddenInput

class FormMixin(object):
    metadata = {}
    metadata_attr_targets = ['max_length', 'max_value', 'min_length', 'min_value', 'required']
    metadata_processors = defaultdict(list)
    
    def __getitem__(self, name):
        return self._bind_field(name, self.fields[name])
    
    def __iter__(self):
        for name, field in self.fields.items():
            if not getattr(field, 'omitted', False):
                yield self._bind_field(name, field)
            
    def add_error(self, field, message):
        self._errors.setdefault(field, ErrorList()).append(message)
        
    def hide(self, field, value=None, required=None):
        self.fields[field].widget = HiddenInput()
        if value is not None:
            self.initial[field] = value
        if required is not None:
            self.fields[field].required = required
        return self
    
    def omit(self, field):
        self.fields[field].omitted = True
        self.fields[field].required = False
        return self
        
    def require(self, field, required=True):
        self.fields[field].required = required
        return self
    
    def specify(self, field, value=None):
        if value is not None:
            self.initial[field] = value
        return self
    
    def todict(self):
        return dict(self.cleaned_data)
    
    def _bind_field(self, name, field):
        bound = BoundField(self, field, name)
        bound.metadata = self._prepare_field_metadata(name, field)
        
        value = self._get_field_value(bound)
        if isinstance(field, forms.ModelMultipleChoiceField):
            if value:
                ref = [field.queryset.get(pk=val) for val in value if val]
            else:
                ref = []
        elif isinstance(field, forms.ModelChoiceField):
            ref = (field.queryset.get(pk=value) if value else None)
        else:
            ref = value
            
        bound.initial_value = {'value': value, 'ref': ref}
        return bound
    
    def _get_field_value(self, bound):
        if self.is_bound:
            if isinstance(bound.field, forms.FileField) and bound.data is None:
                value = self.initial.get(bound.name, bound.field.initial)
            else:
                value = bound.data
        else:
            value = self.initial.get(bound.name, bound.field.initial)
            if callable(value):
                value = value()
        return bound.field.prepare_value(value)
    
    def _initialize_metadata(self):
        self._field_metadata = self.metadata.get('fields') or {}
        for field, metadata in self._field_metadata.iteritems():
            if field in self.fields:
                required = metadata.get('required', None)
                if required is not None:
                    self.fields[field].required = required
                if metadata.get('hidden', False):
                    self.fields[field].widget = HiddenInput()
    
    def _prepare_field_metadata(self, name, field):
        metadata = self._field_metadata.get(name) or {}
        for target in self.metadata_attr_targets:
            value = getattr(field, target, None)
            if value is not None:
                metadata[target] = value
                
        field_type = type(field).__name__
        for processor in self.metadata_processors.get(field_type, ()):
            processor(metadata, field_type, field)
        return metadata
    
    def metadata_processor(classnames, processors=metadata_processors):
        def decorator(method):
            for classname in classnames:
                processors[classname].append(method)
            return method
        return decorator
    
    @metadata_processor(['IntegerField'])
    def _process_number_fields(metadata, field_type, field):
        metadata.update(datatype='number')
        if field_type == 'IntegerField':
            metadata['decimal_places'] = 0
    
    @metadata_processor(['SlugField'])
    def _process_slugfield(metadata, field_type, field):
        metadata['datatype'] = 'slug'
        metadata['pattern'] = '^[-A-Za-z0-9_]*$'
    
class Form(FormMixin, forms.Form):
    def __init__(self, *args, **params):
        super(Form, self).__init__(*args, **params)
        self._initialize_metadata()
        
class ModelForm(FormMixin, forms.ModelForm):
    def __init__(self, *args, **params):
        self._instance_specified = bool(params.get('instance'))
        super(ModelForm, self).__init__(*args, **params)
        
        self._initialize_metadata()
        if not self._instance_specified:
            self.omit(self._meta.model._meta.pk.name)
        
    def create(self, clean=False, exclusions=None, m2m=True, **params):
        return self._meta.model._default_manager.create_with_mapping(self.todict(),
            clean=clean, exclusions=exclusions, m2m=m2m, **params)
    
    def create_or_update(self, clean=False, exclusions=None, m2m=True, **params):
        method = (self.update if self._instance_specified else self.create)
        return method(clean=clean, exclusions=exclusions, m2m=m2m, **params)
    
    def update(self, clean=False, exclusions=None, m2m=True, **params):
        return self._meta.model._default_manager.update_with_mapping(self.instance, self.todict(),
            clean=clean, exclusions=exclusions, m2m=m2m, **params)
        
    def _post_clean(self):
        pass
    
