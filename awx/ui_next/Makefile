ui_next_mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
ui_next_dir := $(shell realpath --relative-to $(CURDIR) $(dir $(ui_next_mkfile_path)))

ANSIBLE_UI_DIR ?= $(ui_next_dir)/src

ANSIBLE_UI_GIT_REPO_HTTPS ?=
ANSIBLE_UI_GIT_REPO_SSH ?=
ANSIBLE_UI_GIT_BRANCH ?= main

ANSIBLE_UI_LOCAL ?=

.PHONY: ui_next/clone-https
## Shallow clone the ui_next repo via https skip if ANSIBLE_UI_GIT_REPO_HTTPS is undefined
ui_next/clone-https:
	@if [ -z "$(ANSIBLE_UI_GIT_REPO_HTTPS)" ]; then \
		echo "SKIP: ui_next/clone-https. ANSIBLE_UI_GIT_REPO_HTTPS is not set."; \
	elif [ -d "$(ANSIBLE_UI_DIR)" ]; then \
		echo "SKIP: ui_next/clone-https. $(ANSIBLE_UI_DIR) already exists."; \
	else \
		git clone --depth 1 --branch $(ANSIBLE_UI_GIT_BRANCH) $(ANSIBLE_UI_GIT_REPO_HTTPS) $(ANSIBLE_UI_DIR) || true; \
	fi

.PHONY: ui_next/clone-ssh
## Shallow clone the ui_next repo via ssh.
ui_next/clone-ssh:
	@if [ -z "$(ANSIBLE_UI_GIT_REPO_SSH)" ]; then \
		echo "SKIP: ui_next/clone-ssh. ANSIBLE_UI_GIT_REPO_SSH is not set."; \
	elif [ -d "$(ANSIBLE_UI_DIR)" ]; then \
		echo "SKIP: ui_next/clone-ssh. $(ANSIBLE_UI_DIR) already exists."; \
	else \
		git clone --depth 1 --branch $(ANSIBLE_UI_GIT_BRANCH) $(ANSIBLE_UI_GIT_REPO_SSH) $(ANSIBLE_UI_DIR) || true; \
	fi

.PHONY: ui_next/link-local
## Link to a existing local clone of ui_next repo.
ui_next/link-local:
	@if [ -z "$(ANSIBLE_UI_LOCAL)" ]; then \
		echo "SKIP: ui_next/link-local. ANSIBLE_UI_LOCAL is not set."; \
	elif [ -d "$(ANSIBLE_UI_DIR)" ]; then \
		echo "SKIP: ui_next/link-local. $(ANSIBLE_UI_DIR) already exists."; \
	else \
		ln -s $(ANSIBLE_UI_LOCAL) $(ANSIBLE_UI_DIR); \
	fi

.PHONY: ui_next
## Try to link to a local clone of ui_next repo if it exist otherwise clone via ssh than https.
ui_next:
	@if [ -d "$(ANSIBLE_UI_DIR)" ]; then \
		echo "SKIP: ui_next. $(ANSIBLE_UI_DIR) already exists."; \
	else \
		$(MAKE) ui_next/link-local ui_next/clone-ssh ui_next/clone-https; \
	fi

## Alias for ui_next, will not run if ui_next already exist
$(ANSIBLE_UI_DIR):
	$(MAKE) ui_next

.PHONY: ui_next/build
## Build ui_next
ui_next/build: ui_next
	cd $(ANSIBLE_UI_DIR) && \
	npm install webpack && \
	npm run build:awx

## Alias for ui_next/build, will not run if build already exist
$(ANSIBLE_UI_DIR)/build:
	$(MAKE) ui_next/build

.PHONY: ui_next/clean
## Clean ui_next
ui_next/clean:
	rm -rf $(UI_NEXT_BUILD_FLAG_FILE)
	rm -rf $(ANSIBLE_UI_DIR)

.PHONY: ui_next/clean/build
## Clean ui_next build
ui_next/clean/build:
	rm -rf $(UI_NEXT_BUILD_FLAG_FILE)
	rm -rf $(ANSIBLE_UI_DIR)/build

