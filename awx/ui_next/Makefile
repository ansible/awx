UI_NEXT_MKFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
UI_NEXT_DIR := $(shell realpath --relative-to $(CURDIR) $(dir $(UI_NEXT_MKFILE_PATH)))

UI_NEXT_SRC_DIR := $(UI_NEXT_DIR)/src

UI_NEXT_SRC_GIT_REPO_HTTPS ?=
UI_NEXT_SRC_GIT_REPO_SSH ?=
UI_NEXT_SRC_GIT_BRANCH ?= main

UI_NEXT_LOCAL ?=

.PHONY: ui_next/clone-https
## Shallow clone the ui_next repo via https skip if UI_NEXT_SRC_GIT_REPO_HTTPS is undefined
ui_next/clone-https:
	@if [ -z "$(UI_NEXT_SRC_GIT_REPO_HTTPS)" ]; then \
		echo "SKIP: ui_next/clone-https. UI_NEXT_SRC_GIT_REPO_HTTPS is not set."; \
	elif [ -d "$(UI_NEXT_SRC_DIR)" ]; then \
		echo "SKIP: ui_next/clone-https. $(UI_NEXT_SRC_DIR) already exists."; \
	else \
		git clone --depth 1 --branch $(UI_NEXT_SRC_GIT_BRANCH) $(UI_NEXT_SRC_GIT_REPO_HTTPS) $(UI_NEXT_SRC_DIR) || true; \
	fi

.PHONY: ui_next/clone-ssh
## Shallow clone the ui_next repo via ssh.
ui_next/clone-ssh:
	@if [ -z "$(UI_NEXT_SRC_GIT_REPO_SSH)" ]; then \
		echo "SKIP: ui_next/clone-ssh. UI_NEXT_SRC_GIT_REPO_SSH is not set."; \
	elif [ -d "$(UI_NEXT_SRC_DIR)" ]; then \
		echo "SKIP: ui_next/clone-ssh. $(UI_NEXT_SRC_DIR) already exists."; \
	else \
		git clone --depth 1 --branch $(UI_NEXT_SRC_GIT_BRANCH) $(UI_NEXT_SRC_GIT_REPO_SSH) $(UI_NEXT_SRC_DIR) || true; \
	fi

.PHONY: ui_next/link-local
## Link to a existing local clone of ui_next repo.
ui_next/link-local:
	@if [ -z "$(UI_NEXT_LOCAL)" ]; then \
		echo "SKIP: ui_next/link-local. UI_NEXT_LOCAL is not set."; \
	elif [ -d "$(UI_NEXT_SRC_DIR)" ]; then \
		echo "SKIP: ui_next/link-local. $(UI_NEXT_SRC_DIR) already exists."; \
	else \
		ln -s $(UI_NEXT_LOCAL) $(UI_NEXT_SRC_DIR); \
	fi

.PHONY: ui_next
## Try to link to a local clone of ui_next repo if it exist otherwise clone via ssh than https.
ui_next:
	@if [ -d "$(UI_NEXT_SRC_DIR)" ]; then \
		echo "SKIP: ui_next. $(UI_NEXT_SRC_DIR) already exists."; \
	else \
		$(MAKE) ui_next/link-local ui_next/clone-ssh ui_next/clone-https; \
	fi

## Alias for ui_next, will not run if ui_next already exist
$(UI_NEXT_SRC_DIR):
	$(MAKE) ui_next

.PHONY: ui_next/build
## Build ui_next
ui_next/build: ui_next
	cd $(UI_NEXT_SRC_DIR) && \
	npm install webpack && \
	npm run build:awx && \
	mv build ../

## Alias for ui_next/build, will not run if build already exist
$(UI_NEXT_DIR)/build:
	$(MAKE) ui_next/build

.PHONY: ui_next/clean
## Clean ui_next
ui_next/clean: ui_next/clean/build
	rm -rf $(UI_NEXT_SRC_DIR)

.PHONY: ui_next/clean/build
## Clean ui_next build
ui_next/clean/build:
	rm -rf $$(UI_NEXT_DIR)/build

