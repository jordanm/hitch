import logging

from django.core.urlresolvers import reverse

from hitch.core.league import forms
from hitch.core.league.models import Season, Team
from hitch.core.views import Views
from hitch.support.views import viewable

log = logging.getLogger(__name__)

class LeagueViews(Views):
    @viewable('modify-season', r'^a/modify-season', ajax_only=True, authenticated=True)
    def modify_season(self, request, response):
        response.authorize('modify-season')
        try:
            season = Season.objects.get(id=request.REQUEST['id'])
        except KeyError:
            season = None
        except Season.DoesNotExist:
            if request.posting:
                return response.error('object-not-found').json()
            else:
                return response.ignore()
            
        if request.posting:
            form = forms.SeasonForm(data=request.POST, instance=season)
            if form.is_valid():
                try:
                    season = form.create_or_update(clean=True)
                except Exception:
                    log.exception('unhandled exception during season modification')
                    response.message('An unknown error has occurred.', 'error')
                    return response.error().json()
                else:
                    return response.json(id=season.id, url=reverse('season', args=[season.name])) 
            else:
                return response.collect(form).error('invalid-submission').json()
        else:
            form = forms.SeasonForm(instance=season)
            return response.render('league/modal-modify-season.html', form=form)

    @viewable('modify-team', r'^a/modify-team')
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
        
    @viewable('season', r'^season/(?P<name>\w+)')
    def season(self, request, response, name):
        try:
            season = Season.objects.get(name=name)
        except Season.DoesNotExist:
            return response.redirect()
        
        return response.render('league/season.html', season=season)
    
    @viewable('seasons', r'^seasons')
    def seasons(self, request, response):
        return response.render('league/seasons.html')