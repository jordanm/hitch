import logging
from datetime import datetime

from django.conf import settings
from django.db import models

from hitch.support.models import CharField, Manager, Model, SlugField, UniqueIdentifierField
from hitch.support.util import choices

class ScoringPolicy(Model):
    class Meta:
        app_label = 'core'
        
    id = UniqueIdentifierField()
    name = CharField('Name', unique=True)
    
    def __unicode__(self):
        return self.name

class Season(Model):
    class Meta:
        app_label = 'core'
    
    StatusTokens = ('planned', 'active', 'finished')
        
    id = UniqueIdentifierField()
    status = CharField('Status', choices=choices(StatusTokens), default='planned')
    name = SlugField('Name', unique=True)
    title = CharField('Title')
    start_date = models.DateField('Start date', null=True, blank=True)
    end_date = models.DateField('End date', null=True, blank=True)
    match_count = models.IntegerField('Match count', default=0)
    scoring_policy = models.ForeignKey(ScoringPolicy, null=True, blank=True)
    
    def __unicode__(self):
        return self.name
    
class Team(Model):
    class Meta:
        app_label = 'core'
        unique_together = ('season', 'name')
    
    StatusTokens = ('active', 'inactive')
        
    id = UniqueIdentifierField()
    season = models.ForeignKey(Season, related_name='teams')
    name = SlugField('Name')
    title = CharField('Title')
    status = CharField('Status', choices=choices(StatusTokens), default='active')
    
    def __unicode__(self):
        return self.name
    
class Member(Model):
    class Meta:
        app_label = 'core'
        unique_together = ('season', 'team', 'account')
        
    id = UniqueIdentifierField()
    season = models.ForeignKey(Season, related_name='members')
    team = models.ForeignKey(Team, related_name='_members')
    account = models.ForeignKey('core.Account')
    
    def __unicode__(self):
        return '%s - %s' % (self.team.name, self.account.fullname)
    
class Match(Model):
    class Meta:
        app_label = 'core'
        unique_together = ('season', 'match', 'home_team', 'away_team')
        
    id = UniqueIdentifierField()
    season = models.ForeignKey(Season, related_name='matches')
    match = models.IntegerField('Match')
    home_team = models.ForeignKey(Team, related_name='home_matches')
    away_team = models.ForeignKey(Team, related_name='away_matches')
    occurrence = models.DateField('Occurrence', null=True, blank=True)
    
    def __unicode__(self):
        return '%s v %s' % (self.home_team.name, self.away_team.name)
    
class Round(Model):
    class Meta:
        app_label = 'core'
        unique_together = ('match', 'round')
        
    id = UniqueIdentifierField()
    match = models.ForeignKey(Match, related_name='rounds')
    round = models.IntegerField('Round')
    home_points = models.IntegerField('Home points')
    away_points = models.IntegerField('Away points')
    
    def __unicode__(self):
        return '%s (round %d)' % (self.match, self.round)