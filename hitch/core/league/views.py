import logging

from django.core.urlresolvers import reverse

from hitch.core.league import forms
from hitch.core.league.models import Season, Team
from hitch.core.views import Views
from hitch.support.views import viewable

log = logging.getLogger(__name__)

class LeagueViews(Views):
    @viewable('modify-team', r'a/modify-team')
    def modify_team(self, request, response):
        try:
            team = Team.objects.get(id=request.REQUEST['id'])
        except KeyError:
            team = None
        except Team.DoesNotExist:
            if request.posting:
                return response.error('unknown-object').json()
            else:
                return response.ignore()
        
        if request.posting:
            pass
        else:
            form = forms.TeamForm(2)
            return response.render('league/modal-team.html', form=form)
        
    @viewable('season', r'season/(?P<name>\w+)')
    def season(self, request, response, name):
        try:
            season = Season.objects.get(name=name)
        except Season.DoesNotExist:
            return response.redirect()
        
        return response.render('league/season.html', season=season)