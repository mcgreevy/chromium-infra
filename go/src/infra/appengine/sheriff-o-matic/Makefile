.PHONY: test
WCT_PATH = ./node_modules/web-component-tester/bin/wct
VULCANIZE_PATH = ./node_modules/vulcanize/bin/vulcanize

default: help

help:
	@echo "Available commands:"
	@sed -n '/^[a-zA-Z0-9_]*:/s/:.*//p' <Makefile

deps:
	bower install
	npm install

format:
	gofmt -s -w .
	clang-format -i elements/**/*.js -style=file

lint:
	polylint -i elements/som-app/som-app.html

build: deps
	$(VULCANIZE_PATH) elements/som-app/som-app.html -o elements/som-app/som-app.vulcanized.html --inline-scripts

clean:
	rm elements/som-app/som-app.vulcanized.html

test: deps
	cd som && go test --cover
	xvfb-run -a $(WCT_PATH)

relnotes:
	go run ../../tools/relnotes/relnotes.go -app sheriff-o-matic . ../../monitoring/analyzer ../../monitoring/client ../../monitoring/messages

# This is only used for testing on the continuous build system.
bower-cipd: deps
	cipd pkg-build -pkg-def ./cipd/sheriff-o-matic.yaml -pkg-var platform:linux-amd64 -out ./cipd/bower_components.cipd
	cipd pkg-register ./cipd/bower_components.cipd

# In the future we can add different commends for prod and staging.
deploy-prod: build
	./gae.py upload -A sheriff-o-matic
	rm elements/som-app/som-app.vulcanized.html

deploy: build
	./gae.py upload
	rm elements/som-app/som-app.vulcanized.html
