.PHONY: all main lint lessc

all: clean lessc lint main istanbul

clean:
	rm -rf src-instrumented
	rm -f js/bundle.js
	rm -f css/style.css

main:
	webpack

lint:
	jshint --verbose src/*js

lessc:
	lessc src/style.less css/style.css

istanbul:
	istanbul instrument --output src-instrumented src
	webpack src-instrumented/main.js  js/bundle-instrumented.js
	cp index.html index-instrumented.html
	sed -i "s/bundle.js/bundle-instrumented.js/g" index-instrumented.html
	cp vendor/*.js js/
