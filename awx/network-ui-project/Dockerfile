
FROM python:2.7
ENV PYTHONUNBUFFERED 1

# Requirements have to be pulled and installed here, otherwise caching won't work
COPY ./requirements /requirements

RUN pip install -r /requirements/production.txt

RUN groupadd -r django && useradd -r -g django django
COPY . /app
RUN chown -R django /app

COPY ./compose/django/gunicorn.sh /gunicorn.sh
COPY ./compose/django/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh && chown django /entrypoint.sh
RUN chmod +x /gunicorn.sh && chown django /gunicorn.sh

WORKDIR /app

ENTRYPOINT ["/entrypoint.sh"]
