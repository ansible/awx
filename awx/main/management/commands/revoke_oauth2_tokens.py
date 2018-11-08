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
        print('revoked {} {}'.format(token.__class__.__name__, token.token))


class Command(BaseCommand):
    """Command that revokes OAuth2 access tokens."""
    help='Revokes OAuth2 access tokens.  Use --all to revoke access and refresh tokens.'

    def add_arguments(self, parser):
        parser.add_argument('--user', dest='user', type=str, help='revoke OAuth2 tokens for a specific username')
        parser.add_argument('--all', dest='all', action='store_true', help='revoke OAuth2 access tokens and refresh tokens')

    def handle(self, *args, **options):
        if not options['user']:
            if options['all']:
                revoke_tokens(RefreshToken.objects.filter(revoked=None))
            revoke_tokens(OAuth2AccessToken.objects.all())
        else:
            try:
                user = User.objects.get(username=options['user'])
            except ObjectDoesNotExist:
                raise CommandError('A user with that username does not exist.')
            if options['all']:
                revoke_tokens(RefreshToken.objects.filter(revoked=None).filter(user=user))
            revoke_tokens(user.main_oauth2accesstoken.filter(user=user))
