
SERVER = "https://meganuke:8043"
PORT = "9000"

.PHONY: clean coverage

clean:
	git clean -fdX .
	git clean -fd .

coverage:
	./coverage_report.py ${SERVER}
	python -m SimpleHTTPServer ${PORT}
