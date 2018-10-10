# Django
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

# AWX
from awx.api.serializers import OAuth2TokenSerializer


class Command(BaseCommand):
    """Command that creates an OAuth2 token for a certain user. Returns the value of created token."""
    help='Creates an OAuth2 token for a user.'

    def add_arguments(self, parser):
        parser.add_argument('--user', dest='user', type=str)

    def handle(self, *args, **options):
        if not options['user']:

            raise CommandError('Username not supplied. Usage: awx-manage create_oauth2_token --user=username.')
        try:
            user = User.objects.get(username=options['user'])
        except ObjectDoesNotExist:
            raise CommandError('The user does not exist.')
        config = {'user': user, 'scope':'write'}
        serializer_obj = OAuth2TokenSerializer()

        class FakeRequest(object):
            def __init__(self):
                self.user = user

        serializer_obj.context['request'] = FakeRequest()
        token_record = serializer_obj.create(config)
        self.stdout.write(token_record.token)
