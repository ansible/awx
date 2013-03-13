clean:
	find . -type f -regex ".*\.py[co]$$" -delete

setup:
	ansible-playbook app_setup/setup.yml -i "127.0.0.1," -c local -e working_dir=`pwd`

syncdb:
	python acom/manage.py syncdb

runserver:
	python acom/manage.py runserver

# already done and should not have to happen again:
#
#south_init:
#	PYTHON_PATH=./acom python acom/manage.py schemamigration main --initial

dbchange:
	PYTHON_PATH=./acom python acom/manage.py schemamigration main --auto

migrate:
	PYTHON_PATH=./acom python acom/manage.py migrate main --auto

test:
	PYTHON_PATH=./acom python acom/manage.py test main
         
