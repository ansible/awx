ui_next_mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
ui_next_dir := $(shell realpath --relative-to $(CURDIR) $(dir $(ui_next_mkfile_path)))

ANSIBLE_UI_DIR ?= $(ui_next_dir)/src

ANSIBLE_UI_GIT_REPO_HTTPS ?=
ANSIBLE_UI_GIT_REPO_SSH ?=
ANSIBLE_UI_GIT_BRANCH ?= main

ANSIBLE_UI_LOCAL ?=

.PHONY: ui-next/clone-https
## Shallow clone the ui-next repo via https skip if ANSIBLE_UI_GIT_REPO_HTTPS is undefined
ui-next/clone-https:
	@if [ -z "$(ANSIBLE_UI_GIT_REPO_HTTPS)" ]; then \
		echo "SKIP: ui-next/clone-https. ANSIBLE_UI_GIT_REPO_HTTPS is not set."; \
	elif [ -d "$(ANSIBLE_UI_DIR)" ]; then \
		echo "SKIP: ui-next/clone-https. $(ANSIBLE_UI_DIR) already exists."; \
	else \
		git clone --depth 1 --branch $(ANSIBLE_UI_GIT_BRANCH) $(ANSIBLE_UI_GIT_REPO_HTTPS) $(ANSIBLE_UI_DIR) || true; \
	fi

.PHONY: ui-next/clone-ssh
## Shallow clone the ui-next repo via ssh.
ui-next/clone-ssh:
	@if [ -z "$(ANSIBLE_UI_GIT_REPO_SSH)" ]; then \
		echo "SKIP: ui-next/clone-ssh. ANSIBLE_UI_GIT_REPO_SSH is not set."; \
	elif [ -d "$(ANSIBLE_UI_DIR)" ]; then \
		echo "SKIP: ui-next/clone-ssh. $(ANSIBLE_UI_DIR) already exists."; \
	else \
		git clone --depth 1 --branch $(ANSIBLE_UI_GIT_BRANCH) $(ANSIBLE_UI_GIT_REPO_SSH) $(ANSIBLE_UI_DIR) || true; \
	fi

.PHONY: ui-next/link-local
## Link to a existing local clone of ui-next repo.
ui-next/link-local:
	@if [ -z "$(ANSIBLE_UI_LOCAL)" ]; then \
		echo "SKIP: ui-next/link-local. ANSIBLE_UI_LOCAL is not set."; \
	elif [ -d "$(ANSIBLE_UI_DIR)" ]; then \
		echo "SKIP: ui-next/link-local. $(ANSIBLE_UI_DIR) already exists."; \
	else \
		ln -s $(ANSIBLE_UI_LOCAL) $(ANSIBLE_UI_DIR); \
	fi

.PHONY: ui-next
## Try to link to a local clone of ui-next repo if it exist otherwise clone via ssh than https.
ui-next:
	@if [ -d "$(ANSIBLE_UI_DIR)" ]; then \
		echo "SKIP: ui-next. $(ANSIBLE_UI_DIR) already exists."; \
	else \
		$(MAKE) ui-next/link-local ui-next/clone-ssh ui-next/clone-https; \
	fi

## Alias for ui-next, will not run if ui-next already exist
$(ANSIBLE_UI_DIR):
	$(MAKE) ui-next

.PHONY: ui-next/build
## Build ui-next
ui-next/build: ui-next
	cd $(ANSIBLE_UI_DIR) && \
	npm install webpack && \
	npm run build:controller

## Alias for ui-next/build, will not run if build already exist
$(ANSIBLE_UI_DIR)/build:
	$(MAKE) ui-next/build

.PHONY: ui-next/clean
## Clean ui-next
ui-next/clean:
	rm -rf $(UI_NEXT_BUILD_FLAG_FILE)
	rm -rf $(ANSIBLE_UI_DIR)

.PHONY: ui-next/clean/build
## Clean ui-next build
ui-next/clean/build:
	rm -rf $(UI_NEXT_BUILD_FLAG_FILE)
	rm -rf $(ANSIBLE_UI_DIR)/build

