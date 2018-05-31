from awx.api.serializers import OAuth2TokenSerializer
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist


class Command(BaseCommand):
    """Command that creates an OAuth2 token for a certain user. Returns the value of created token."""
    help='Usage: awx-manage create_oauth2_token --user=username. Will return the value of created token.'

    def add_arguments(self, parser):
        parser.add_argument('--user', dest='user', type=str)

    def handle(self, *args, **options):
        if not options['user']:
            self.stdout.write("Username not supplied. Usage: awx-manage create_oauth2_token --user=username.")
            return
        try:
            user = User.objects.get(username=options['user'])
        except ObjectDoesNotExist:
            self.stdout.write("The user does not exist.")
            return
        config = {'user': user, 'scope':'write'}
        serializer_obj = OAuth2TokenSerializer()
        token_record = serializer_obj.create(config, True)
        self.stdout.write(token_record.token)
