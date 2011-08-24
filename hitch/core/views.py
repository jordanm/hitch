from hitch.support.views import ViewSet, viewable

class Views(ViewSet):
    @viewable('index', r'^$')
    def index(self, request, response):
        return response.render('index.html')

from .account.views import *
from .league.views import *