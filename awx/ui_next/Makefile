UI_NEXT_MKFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
UI_NEXT_MKFILE_DIR := $(dir $(UI_NEXT_MKFILE_PATH))
UI_NEXT_DIR := $(subst $(CURDIR)/,, $(UI_NEXT_MKFILE_DIR))

# NOTE: UI_NEXT_DIR swallowed the / because we want to be able to run `make src` from the ui_next dir
UI_NEXT_SRC_DIR := $(UI_NEXT_DIR)src
UI_NEXT_BUILD_DIR := $(UI_NEXT_DIR)build

# Path to your local clone of the UI_NEXT repo
UI_NEXT_LOCAL ?=

# Git repo and branch to the UI_NEXT repo
UI_NEXT_GIT_REPO_SSH ?= git@github.com:ansible/ansible-ui.git
UI_NEXT_GIT_REPO_HTTPS ?= https://github.com/ansible/ansible-ui.git
UI_NEXT_GIT_BRANCH ?= main


.PHONY: ui_next/clone-https
## Shallow clone the ui_next repo via https skip if UI_NEXT_GIT_REPO_HTTPS is undefined
ui_next/clone-https:
	@if [ -z "$(UI_NEXT_GIT_REPO_HTTPS)" ]; then \
		echo "SKIP: ui_next/clone-https. UI_NEXT_GIT_REPO_HTTPS is not set."; \
	elif [ -d "$(UI_NEXT_SRC_DIR)" ]; then \
		echo "SKIP: ui_next/clone-https. $(UI_NEXT_SRC_DIR) already exists."; \
	else \
		git clone --depth 1 --branch $(UI_NEXT_GIT_BRANCH) $(UI_NEXT_GIT_REPO_HTTPS) $(UI_NEXT_SRC_DIR) || true; \
	fi

.PHONY: ui_next/clone-ssh
## Shallow clone the ui_next repo via ssh.
ui_next/clone-ssh:
	@if [ -z "$(UI_NEXT_GIT_REPO_SSH)" ]; then \
		echo "SKIP: ui_next/clone-ssh. UI_NEXT_GIT_REPO_SSH is not set."; \
	elif [ -d "$(UI_NEXT_SRC_DIR)" ]; then \
		echo "SKIP: ui_next/clone-ssh. $(UI_NEXT_SRC_DIR) already exists."; \
	else \
		git clone --depth 1 --branch $(UI_NEXT_GIT_BRANCH) $(UI_NEXT_GIT_REPO_SSH) $(UI_NEXT_SRC_DIR) || true; \
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

.PHONY: ui_next/src
## Try to link to a local clone of ui_next repo if it exist otherwise clone via ssh than https.
ui_next/src:
	@if [ -d "$(UI_NEXT_SRC_DIR)" ]; then \
		echo "SKIP: ui_next. $(UI_NEXT_SRC_DIR) already exists."; \
	else \
		$(MAKE) ui_next/link-local ui_next/clone-ssh ui_next/clone-https; \
	fi

## Alias for ui_next, will not run if ui_next already exist
$(UI_NEXT_SRC_DIR):
	$(MAKE) ui_next/src

.PHONY: ui_next/build
## Build ui_next from source
ui_next/src/build: ui_next/src
	cd $(UI_NEXT_SRC_DIR) && \
	npm install webpack && \
	npm run build:awx

.PHONY: ui_next/build
## Copy ui_next/src/build to ui_next/build
ui_next/build: ui_next/src/build
	cp -r $(UI_NEXT_SRC_DIR)/build $(UI_NEXT_BUILD_DIR)

## Alias for ui_next/build, will not run if build already exist
$(UI_NEXT_BUILD_DIR):
	$(MAKE) ui_next/build

## Alias for ui_next/clean
$(UI_NEXT_DIR)clean:
	rm -rf $(UI_NEXT_DIR)/src
	rm -rf $(UI_NEXT_DIR)/build

.PHONY: ui_next/clean
## Clean ui_next
ui_next/clean: ui_next/clean/build
	rm -rf $(UI_NEXT_DIR)/src

.PHONY: ui_next/clean/src
## Clean ui_next src
ui_next/clean/src:
	rm -rf $(UI_NEXT_DIR)/src

.PHONY: ui_next/clean/build
## Clean ui_next build
ui_next/clean/build:
	rm -rf $(UI_NEXT_DIR)/build

print-%:
	@echo $($*)