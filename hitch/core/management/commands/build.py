from optparse import make_option
from traceback import print_exc

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from hitch.support.css import build_css_targets

class Command(BaseCommand):
    help = 'Builds the site.'
    option_list = BaseCommand.option_list + (
        make_option('-m', '--minified', action='store_true', dest='minified',
            default=False, help='Minify css.'),
        make_option('-s', '--stdout', action='store_true', dest='stdout',
            default=False, help='Pipe output to stdout instead.'),
    )
    
    def handle(self, *args, **params):
        build_css_targets(args, minified=params['minified'], stdout=params['stdout'])