## UI_DIR: Relative path to the directory containing this Makefile
UI_DIR := $(patsubst %/,%,$(dir $(lastword $(MAKEFILE_LIST))))

## Path to your local clone of the UI repo
#  NOTE: you will not be able to build within the docker-compose development environment if you use this option
UI_LOCAL ?=

## Git repo and branch to the UI repo
UI_GIT_REPO ?= https://github.com/ansible/ansible-ui.git
UI_GIT_BRANCH ?= main

## Product name to display on the UI used in UI build process
PRODUCT ?= AWX

.PHONY: ui
## Default build target of ui Makefile, builds ui/build
ui: ui/build

.PHONY: ui/build
## Build ui/build
ui/build: $(UI_DIR)/build

## True build target for ui.
$(UI_DIR)/build:
	@$(MAKE) $(UI_DIR)/src/build/awx
	@echo "=== Copying $(UI_DIR)/src/build to $(UI_DIR)/build ==="
	@rm -rf $(UI_DIR)/build
	@cp -r $(UI_DIR)/src/build $(UI_DIR)
	@echo "=== Done building $(UI_DIR)/build ==="

.PHONY: ui/src/build
## Build ui/src/build
ui/src/build: $(UI_DIR)/src/build/awx

## True target for ui/src/build. Build ui from source.
$(UI_DIR)/src/build/awx: $(UI_DIR)/src $(UI_DIR)/src/node_modules/webpack
	@echo "=== Building ui ==="
	@cd $(UI_DIR)/src && PRODUCT="$(PRODUCT)" PUBLIC_PATH=/static/awx/ ROUTE_PREFIX=/ npm run build:awx
	@mv $(UI_DIR)/src/build/awx/index.html $(UI_DIR)/src/build/awx/index_awx.html

.PHONY: ui/src
## Clone or link src of UI to ui/src, will re-clone/link/update if necessary.
ui/src: $(UI_DIR)/src

# TODO: Rewrite this big bash script in a more readable way.
## True target for ui/src.
$(UI_DIR)/src:
	@echo "=== Setting up $(UI_DIR)/src ==="
	@if [ ! -z "$(UI_LOCAL)" ]; then \
		if [ -d $(UI_DIR)/src ]; then \
			if [ "$$(readlink $(UI_DIR)/src)" = "$(UI_LOCAL)" ]; then \
				echo "SKIP: ui/src. $(UI_DIR)/src already linked to $(UI_LOCAL)."; \
			else \
				echo "=== Linking $(UI_DIR)/src to $(UI_LOCAL) ==="; \
				rm -rf $(UI_DIR)/src; \
				ln -s $(UI_LOCAL) $(UI_DIR)/src; \
			fi; \
		else \
			echo "=== Linking $(UI_DIR)/src to $(UI_LOCAL) ==="; \
			ln -s $(UI_LOCAL) $(UI_DIR)/src; \
		fi; \
	elif [ ! -z "$(UI_GIT_REPO)" ]; then \
		if [ -d $(UI_DIR)/src ]; then \
			GIT_REMOTE_ORIGIN=$$(cd $(UI_DIR)/src && git remote get-url origin); \
			GIT_REMOTE_BRANCH=$$(cd $(UI_DIR)/src && git rev-parse --abbrev-ref HEAD); \
			if [ "$$GIT_REMOTE_ORIGIN" = "$(UI_GIT_REPO)" ] && [ "$$GIT_REMOTE_BRANCH" = "$(UI_GIT_BRANCH)" ]; then \
				echo "=== Updating $(UI_DIR)/src from $(UI_GIT_BRANCH) of $(UI_GIT_REPO) ==="; \
				git fetch && git pull; \
			else \
				echo "=== Cloning $(UI_DIR)/src from $(UI_GIT_BRANCH) of $(UI_GIT_REPO) ==="; \
				rm -rf $(UI_DIR)/src; \
				git clone --depth 1 --branch $(UI_GIT_BRANCH) $(UI_GIT_REPO) $(UI_DIR)/src || true; \
			fi; \
		else \
			echo "=== Cloning $(UI_DIR)/src from $(UI_GIT_BRANCH) of $(UI_GIT_REPO) ==="; \
			git clone --depth 1 --branch $(UI_GIT_BRANCH) $(UI_GIT_REPO) $(UI_DIR)/src || true; \
		fi; \
	else \
		echo "FAILED: ui/src. UI_LOCAL and UI_GIT_REPO are not set."; \
		exit 1; \
	fi

.PHONY: ui/src/webpack
## Install webpack.
ui/src/webpack: $(UI_DIR)/src/node_modules/webpack

## True target for ui/src/webpack.
$(UI_DIR)/src/node_modules/webpack:
	@echo "=== Installing webpack ==="
	@cd $(UI_DIR)/src && npm install webpack

.PHONY: clean/ui
## Clean ui
clean/ui: clean/ui/build clean/ui/src

.PHONY: clean/ui/src
## Clean ui src
clean/ui/src:
	rm -rf $(UI_DIR)/src

.PHONY: clean/ui/build
## Clean ui build
clean/ui/build:
	rm -rf $(UI_DIR)/build

.PHONY: $(UI_DIR)/clean
## Alias for clean/ui, so we can run `make clean` directly in ui
$(UI_DIR)/clean: clean/ui

.PHONY: $(UI_DIR)/clean/src
## Alias for clean/ui/src, so we can run `make clean/src` directly in ui
$(UI_DIR)/clean/src: clean/ui/src

.PHONY: $(UI_DIR)/clean/build
## Alias for clean/ui/build, so we can run `make clean/build` directly in ui
$(UI_DIR)/clean/build: clean/ui/build
