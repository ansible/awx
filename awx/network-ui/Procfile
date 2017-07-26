web: gunicorn config.wsgi:application
worker: celery worker --app=stairmaster.taskapp --loglevel=info
