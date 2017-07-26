

.PHONY: all models admin

all: models admin

models:
	jinja2 templates/models.pyt designs/models.yml > models.py
	autopep8 -i models.py

admin:
	jinja2 templates/admin.pyt designs/models.yml > admin.py
	autopep8 -i admin.py
