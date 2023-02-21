## UI_NEXT_MKFILE_PATH: Path to this Makefile
UI_NEXT_MKFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))

## UI_NEXT_DIR_ABS: Absolute path to the directory containing this Makefile
UI_NEXT_DIR_ABS := $(dir $(UI_NEXT_MKFILE_PATH))

## UI_NEXT_REL_DIR: Relative path to the directory containing this Makefile
#  NOTE: UI_NEXT_REL_DIR swallowed the / because we want to be able to run `make src` from the ui_next dir
UI_NEXT_REL_DIR := $(subst $(CURDIR)/,, $(UI_NEXT_DIR_ABS))

## UI_NEXT_SRC_DIR: Path to the ui_next src directory
UI_NEXT_SRC_DIR := $(UI_NEXT_REL_DIR)src

## UI_NEXT_BUILD_DIR: Path to the ui_next build directory
UI_NEXT_BUILD_DIR := $(UI_NEXT_REL_DIR)build

## Path to your local clone of the UI_NEXT repo
#  NOTE: This does not work with docker-compose development environment
UI_NEXT_LOCAL ?=

# Git repo and branch to the UI_NEXT repo
UI_NEXT_GIT_REPO_SSH ?= git@github.com:ansible/ansible-ui.git
UI_NEXT_GIT_REPO_HTTPS ?= https://github.com/ansible/ansible-ui.git
UI_NEXT_GIT_BRANCH ?= main

# awx-manage collect static require the awx/ui_next/build to exist
# therefore we have to commit the build directory to source control
# so that make docker-compose will be able to start up uwsgi
# UI_NEXT_BUILT_FILE is here so that we can use it as the non-phony build target
UI_NEXT_BUILT_FILE = $(UI_NEXT_REL_DIR).ui-built

## Default target of this Makefile build the ui_next/build from source
ui-next: ui_next/build

.PHONY: ui_next/clone-https
## Shallow clone the ui_next repo via https skip if UI_NEXT_GIT_REPO_HTTPS is undefined
ui_next/clone-https:
	@if [ -z "$(UI_NEXT_GIT_REPO_HTTPS)" ]; then \
		echo "SKIP: ui_next/clone-https. UI_NEXT_GIT_REPO_HTTPS is not set."; \
	elif [ -d $(UI_NEXT_SRC_DIR) ]; then \
		echo "SKIP: ui_next/clone-https. $(UI_NEXT_SRC_DIR) already exists."; \
	else \
		git clone --depth 1 --branch $(UI_NEXT_GIT_BRANCH) $(UI_NEXT_GIT_REPO_HTTPS) $(UI_NEXT_SRC_DIR) || true; \
	fi

.PHONY: ui_next/clone-ssh
## Shallow clone the ui_next repo via ssh.
ui_next/clone-ssh:
	@if [ -z "$(UI_NEXT_GIT_REPO_SSH)" ]; then \
		echo "SKIP: ui_next/clone-ssh. UI_NEXT_GIT_REPO_SSH is not set."; \
	elif [ -d $(UI_NEXT_SRC_DIR) ]; then \
		echo "SKIP: ui_next/clone-ssh. $(UI_NEXT_SRC_DIR) already exists."; \
	else \
		git clone --depth 1 --branch $(UI_NEXT_GIT_BRANCH) $(UI_NEXT_GIT_REPO_SSH) $(UI_NEXT_SRC_DIR) || true; \
	fi

.PHONY: ui_next/link-local
## Link to a existing local clone of ui_next repo. If method will not be able to build inside docker-compose environment
ui_next/link-local:
	@if [ -z "$(UI_NEXT_LOCAL)" ]; then \
		echo "SKIP: ui_next/link-local. UI_NEXT_LOCAL is not set."; \
	elif [ -d $(UI_NEXT_SRC_DIR) ]; then \
		echo "SKIP: ui_next/link-local. $(UI_NEXT_SRC_DIR) already exists."; \
	else \
		ln -s $(UI_NEXT_LOCAL) $(UI_NEXT_SRC_DIR); \
	fi

.PHONY: ui_next/src
## Try to link to a local clone of ui_next repo if it exist otherwise clone via ssh than https.
ui_next/src:
	@if [ -d $(UI_NEXT_SRC_DIR) ]; then \
		echo "SKIP: ui_next. $(UI_NEXT_SRC_DIR) already exists."; \
	else \
		$(MAKE) ui_next/link-local ui_next/clone-ssh ui_next/clone-https; \
	fi

## Alias for ui_next, will not run if ui_next/src already exist
$(UI_NEXT_SRC_DIR):
	$(MAKE) ui_next/src

## Alias for ui_next/build, will not run if ui_next/src/build already exist
$(UI_NEXT_SRC_DIR)/build:
	$(MAKE) ui_next/src/build

.PHONY: ui_next/build
## Build ui_next from source
ui_next/src/build: $(UI_NEXT_SRC_DIR) $(UI_NEXT_SRC_DIR)/node_modules/webpack
	@cd $(UI_NEXT_SRC_DIR) && npm run build:awx


## Install webpack if does not exist.
ui_next/src/node_modules/webpack: $(UI_NEXT_SRC_DIR)
	@if [ -d $(UI_NEXT_SRC_DIR)/node_modules/webpack ]; then \
		echo "SKIP: ui_next/src/node_modules/webpack. $(UI_NEXT_SRC_DIR)/node_modules/webpack already exists."; \
	else \
		cd $(UI_NEXT_SRC_DIR) && npm install webpack; \
	fi

## Alias for ui_next/src/node_modules/webpack. will not run if webpack already exist
$(UI_NEXT_SRC_DIR)/node_modules/webpack:
	$(MAKE) ui_next/src/node_modules/webpack

## Copy ui_next/src/build to ui_next/build
ui_next/build: ui_next/clean/build
	$(MAKE) $(UI_NEXT_SRC_DIR)/build
	@mkdir $(UI_NEXT_DIR_ABS)build && \
	cp -r $(UI_NEXT_SRC_DIR)/build/awx $(UI_NEXT_DIR_ABS)build/awx &&\
	touch $(UI_NEXT_BUILT_FILE)

## Alias for ui_next/build. Will not run if .ui-built file already exist
$(UI_NEXT_BUILT_FILE):
	$(MAKE) ui_next/build

## Alias for ui_next/build.
.PHONY: $(UI_NEXT_BUILD_DIR)
$(UI_NEXT_BUILD_DIR):
	$(MAKE) ui_next/build

.PHONY: $(UI_NEXT_REL_DIR)clean
## Alias for ui_next/clean.
$(UI_NEXT_REL_DIR)clean:
	rm -rf $(UI_NEXT_SRC_DIR)
	rm -rf $(UI_NEXT_BUILD_DIR)

.PHONY: ui_next/clean
## Clean ui_next
ui_next/clean: ui_next/clean/build
	rm -rf $(UI_NEXT_SRC_DIR)

.PHONY: ui_next/clean/src
## Clean ui_next src
ui_next/clean/src:
	rm -rf $(UI_NEXT_SRC_DIR)

.PHONY: ui_next/clean/build
## Clean ui_next build
ui_next/clean/build:
	rm -rf $(UI_NEXT_BUILD_DIR)
	rm -rf $(UI_NEXT_BUILT_FILE)

print-%:
	@echo $($*)