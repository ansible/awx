.PHONY: all main lint lessc install simple-server deploy

all: clean install lessc lint main

clean:
	rm -rf src-instrumented
	rm -f js/bundle.js
	rm -f js/vendor.bundle.js
	rm -f css/style.css

install:
	npm i

main: install
	webpack

lint:
	jshint --verbose src/*js

lessc:
	lessc src/style.less css/style.css

istanbul: main
	istanbul instrument --output src-instrumented src
	webpack --config webpack-instrumented.config.js
	cp index.html index-instrumented.html
	sed -i "s/\/bundle.js/\/bundle-instrumented.js/g" index-instrumented.html
	cp vendor/*.js js/


simple-server: lint main lessc
	python -m SimpleHTTPServer 8081


deploy: main
	rsync -av src/ ../../../../awx/ui/client/src/network_ui/

deploy-instrumented: istanbul
	rsync -av src-instrumented/ ../../../../awx/ui/client/src/network_ui/

extract:
	mkdir -p extracted
	./extract.js ./src/button.js > extracted/button.yml
	./extract.js ./src/buttons.js > extracted/buttons.yml
	./extract.js ./src/device.detail.fsm.js > extracted/device_detail.yml
	./extract.js ./src/group.js > extracted/group.yml
	./extract.js ./src/hotkeys.fsm.js > extracted/hotkeys.yml
	./extract.js ./src/link.js > extracted/link.yml
	./extract.js ./src/mode.fsm.js > extracted/mode.yml
	./extract.js ./src/move.js > extracted/move.yml
	./extract.js ./src/null.fsm.js > extracted/null.yml
	./extract.js ./src/rack.fsm.js > extracted/rack.yml
	./extract.js ./src/site.fsm.js > extracted/site.yml
	./extract.js ./src/stream.fsm.js > extracted/stream.yml
	./extract.js ./src/toolbox.fsm.js > extracted/toolbox.yml
	./extract.js ./src/view.js > extracted/view.yml
	./extract.js ./src/time.js > extracted/time.yml


diff:
	fsm_diff designs/button.yml extracted/button.yml
	fsm_diff designs/buttons.yml extracted/buttons.yml
	fsm_diff designs/device_detail.yml extracted/device_detail.yml
	fsm_diff designs/group.yml extracted/group.yml
	fsm_diff designs/hotkeys.yml extracted/hotkeys.yml
	fsm_diff designs/link.yml extracted/link.yml
	fsm_diff designs/mode.yml extracted/mode.yml
	fsm_diff designs/move.yml extracted/move.yml
	fsm_diff designs/null.yml extracted/null.yml
	fsm_diff designs/rack.yml extracted/rack.yml
	fsm_diff designs/site.yml extracted/site.yml
	fsm_diff designs/stream.yml extracted/stream.yml
	fsm_diff designs/time.yml extracted/time.yml
	fsm_diff designs/toolbox.yml extracted/toolbox.yml
	fsm_diff designs/view.yml extracted/view.yml
