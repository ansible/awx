clean:
	find . -type f -regex ".*\.py[co]$$" -delete

zero:
	python manage.py migrate main zero 

setup:
	ansible-playbook app_setup/setup.yml --verbose -i "127.0.0.1," -c local -e working_dir=`pwd`

syncdb:
	# only run from initial setup
	python manage.py syncdb

runserver:
	# run for testing the server
	python manage.py runserver

# already done and should not have to happen again:
#
south_init:
	python manage.py schemamigration main --initial

dbchange:
	# run this each time we make changes to the model
	python manage.py schemamigration main --auto

migrate:
        # run this to apply changes to the model
	python manage.py migrate

dbshell:
	# access database shell
	# asks for password # PYTHON_PATH=./acom python acom/manage.py dbshell
	sudo -u postgres psql -d acom

test:
	python manage.py test main
         
