
all: build test site

build:
	jison src/jsonlint.y src/jsonlint.l
	mv jsonlint.js lib/jsonlint.js
	node scripts/bundle.js | uglifyjs > web/jsonlint.js

site:
	cp web/jsonlint.js ../jsonlint-pages/jsonlint.js

deploy: site
	cd ../jsonlint-pages && git commit -a -m 'deploy site updates' && git push origin gh-pages

test: lib/jsonlint.js test/all-tests.js
	node test/all-tests.js

