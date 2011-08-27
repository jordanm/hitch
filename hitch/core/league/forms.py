from django import forms
from django.conf import settings

from hitch.core.account.models import Account
from hitch.core.league import models
from hitch.support.forms import Form, ModelForm

class SeasonForm(ModelForm):
    class Meta:
        fields = ('id', 'title', 'name', 'start_date', 'end_date', 'match_count')
        model = models.Season
        
    def __init__(self, **params):
        super(SeasonForm, self).__init__(**params)
        self.hide('id')

class TeamForm(ModelForm):
    class Meta:
        model = models.Team
        
    def __init__(self, member_count=2, **params):
        super(TeamForm, self).__init__(**params)
        self.hide('id', required=False)
        self.hide('season')
        
        self.member_count = member_count
        for i in range(1, member_count + 1):
            self.fields['member%d' % i] = forms.ModelChoiceField(
                queryset=Account.objects.filter(status='active').order_by('fullname'))
        