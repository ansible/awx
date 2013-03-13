clean:
	find . -type f -regex ".*\.py[co]$$" -delete

zero:
	python acom/manage.py migrate main zero 

setup:
	ansible-playbook app_setup/setup.yml --verbose -i "127.0.0.1," -c local -e working_dir=`pwd`

syncdb:
	# only run from initial setup
	python acom/manage.py syncdb

runserver:
	# run for testing the server
	python acom/manage.py runserver

# already done and should not have to happen again:
#
south_init:
	PYTHON_PATH=./acom python acom/manage.py schemamigration main --initial

dbchange:
	# run this each time we make changes to the model
	PYTHON_PATH=./acom python acom/manage.py schemamigration main --auto

migrate:
        # run this to apply changes to the model
	PYTHON_PATH=./acom python acom/manage.py migrate

dbshell:
	# access database shell
	# asks for password # PYTHON_PATH=./acom python acom/manage.py dbshell
	sudo -u postgres psql -d acom

test:
	PYTHON_PATH=./acom python acom/manage.py test main
         
