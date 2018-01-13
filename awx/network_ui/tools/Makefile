
SERVER = "https://meganuke:8043"
PORT = "9000"

.PHONY: coverage

coverage:
	./coverage_report.py ${SERVER}
	python -m SimpleHTTPServer ${PORT}
