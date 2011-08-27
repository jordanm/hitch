import logging
import random
from datetime import datetime

from django.conf import settings
from django.db import models
from django.db.transaction import commit_on_success

from hitch.support.models import CharField, Manager, Model, SlugField, UniqueIdentifierField
from hitch.support.util import choices

def pluck(sequence):
    return (sequence.pop(random.randint(0, len(sequence) - 1)) if sequence else False)

class ScoringPolicy(Model):
    class Meta:
        app_label = 'core'
        
    id = UniqueIdentifierField()
    name = CharField('Name', unique=True)
    round_pts = models.IntegerField('Round Points', null=False)
    spread_pts = models.IntegerField('Spread Points', null=False)
    match_pts = models.IntegerField('Match Points', null=False)
    
    def __unicode__(self):
        return self.name

class Season(Model):
    class Meta:
        app_label = 'core'
    
    StatusTokens = ('planned', 'open', 'active', 'finished')
        
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
    
    @commit_on_success
    def create_team(self, name, title, accounts):
        team = Team.objects.create(season=self, name=name, title=title)
        for account in accounts:
            Member.objects.create(season=season, team=team, account=account)
        return team
    
    def schedule(self):
        teams = list(self.teams.all())
        matches_per_week = len(teams) / 2
        
        byes = []
        matches = {}
        for team in teams:
            matches[team] = []
            
        def _schedule_week():
            week = []
            pool = list(teams)
            random.shuffle(pool)
            while len(pool) >= 2:
                rejects = []
                home = pluck(pool)
                if not home:
                    return False
                away = pluck(pool)
                if not away:
                    return False
                while away in matches[home]:
                    rejects.append(away)
                    away = pluck(pool)
                    if not away:
                        return False
                pool += rejects
                week.append((home, away))
            if len(week) != matches_per_week:
                return False
            if len(pool) == 1:
                if pool[0] in byes:
                    return False
                else:
                    week.append((pool[0],))
                    byes.append(pool[0])
            for match in week:
                if len(match) == 2:
                    matches[match[0]].append(match[1])
                    matches[match[1]].append(match[0])
            return week
        
        schedule = []
        for i in range(1, self.match_count + 1):
            week = _schedule_week()
            while not week:
                week = _schedule_week()
            schedule.append(week)
        return schedule

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

class Week(Model):
    class Meta:
        app_label = 'core'

    id = UniqueIdentifierField()
    season = models.ForeignKey(Season, related_name='weeks')
    week = models.IntegerField('Week')
    date = models.DateField('Week Date', null=False)

    def __unicode__(self):
        return '%s - %d' % (self.season.name, self.week)

class Match(Model):
    class Meta:
        app_label = 'core'
        unique_together = ('season', 'week', 'home_team', 'away_team')
        
    id = UniqueIdentifierField()
    season = models.ForeignKey(Season, related_name='matches')
    week = models.ForeignKey(Week, related_name='matches')
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

