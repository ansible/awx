# Django
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

# AWX
from awx.main.models.oauth import OAuth2AccessToken
from oauth2_provider.models import RefreshToken

def revoke_tokens(token_list):
    for token in token_list:
            token.revoke()

class Command(BaseCommand):
    """Command that revokes OAuth2 tokens and refresh tokens."""
    help='Revokes OAuth2 tokens and refresh tokens.'

    def add_arguments(self, parser):
        parser.add_argument('--user', dest='user', type=str)
        parser.add_argument('--revoke_refresh', dest='revoke_refresh', action='store_true')

    def handle(self, *args, **options):
        if not options['user']:
            if options['revoke_refresh']:
                revoke_tokens(RefreshToken.objects.all())
            revoke_tokens(OAuth2AccessToken.objects.all())
        else:
            try:
                user = User.objects.get(username=options['user'])
            except ObjectDoesNotExist:
                raise CommandError('The user does not exist.')
            if options['revoke_refresh']:
                revoke_tokens(RefreshToken.objects.filter(user=user))
            revoke_tokens(user.main_oauth2accesstoken.filter(user=user))
