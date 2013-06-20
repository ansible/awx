# Django REST Framework
from rest_framework import authentication
from rest_framework import exceptions

# AnsibleWorks
from ansibleworks.main.models import Job

class JobCallbackAuthentication(authentication.BaseAuthentication):
    '''
    Custom authentication used for views accessed by the inventory and callback
    scripts when running a job.
    '''
    
    def authenticate(self, request):
        auth = authentication.get_authorization_header(request).split()
        if len(auth) != 2 or auth[0].lower() != 'token' or '-' not in auth[1]:
            return None
        job_id, job_key = auth[1].split('-', 1)
        try:
            job = Job.objects.get(pk=job_id, status='running')
        except Job.DoesNotExist:
            return None
        token = job.callback_auth_token
        if auth[1] != token:
            raise exceptions.AuthenticationFailed('Invalid job callback token')
        return (None, token)

    def authenticate_header(self, request):
        return 'Token'
