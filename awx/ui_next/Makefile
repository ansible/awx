## UI_NEXT_DIR: Relative path to the directory containing this Makefile
UI_NEXT_DIR := $(patsubst %/,%,$(dir $(lastword $(MAKEFILE_LIST))))

# ## Path to your local clone of the UI_NEXT repo
# #  NOTE: you will not be able to build within the docker-compose development environment if you use this option
UI_NEXT_LOCAL ?=

# Git repo and branch to the UI_NEXT repo
UI_NEXT_GIT_REPO ?= https://github.com/ansible/ansible-ui.git
UI_NEXT_GIT_BRANCH ?= main

.PHONY: ui-next
## Default build target of ui-next Makefile, builds ui-next/build
ui-next: ui-next/build

.PHONY: ui-next/build
## Build ui-next/build
ui-next/build: $(UI_NEXT_DIR)/build
.PHONY: $(UI_NEXT_DIR)/build
## True build target for ui-next.
$(UI_NEXT_DIR)/build: ui-next/src/build
	@echo "=== Copying $(UI_NEXT_DIR)/src/build to $(UI_NEXT_DIR)/build ==="
	@rm -rf $(UI_NEXT_DIR)/build
	@cp -r $(UI_NEXT_DIR)/src/build $(UI_NEXT_DIR)
	@echo "=== Done building $(UI_NEXT_DIR)/build ==="

.PHONY: ui-next/src/build
## Build ui-next/src/build
ui-next/src/build: $(UI_NEXT_DIR)/src/build

.PHONY: $(UI_NEXT_DIR)/src/build
## True target for ui-next/src/build.
$(UI_NEXT_DIR)/src/build: ui-next/src ui-next/src/webpack
	@echo "=== Building ui_next ==="
	@cd $(UI_NEXT_DIR)/src && npm run build:awx

.PHONY: ui-next/src
## Clone or link src of UI_NEXT to ui-next/src, will re-clone/link/update if necessary.
ui-next/src: $(UI_NEXT_DIR)/src

# TODO: Rewrite this big bash script in a more readable way.
.PHONY: $(UI_NEXT_DIR)/src
## True target for ui-next/src.
$(UI_NEXT_DIR)/src:
	@echo "=== Setting up $(UI_NEXT_DIR)/src ==="
	@if [ ! -z "$(UI_NEXT_LOCAL)" ]; then \
		if [ -d $(UI_NEXT_DIR)/src ]; then \
			if [ "$$(readlink $(UI_NEXT_DIR)/src)" = "$(UI_NEXT_LOCAL)" ]; then \
				echo "SKIP: ui-next/src. $(UI_NEXT_DIR)/src already linked to $(UI_NEXT_LOCAL)."; \
			else \
				echo "=== Linking $(UI_NEXT_DIR)/src to $(UI_NEXT_LOCAL) ==="; \
				rm -rf $(UI_NEXT_DIR)/src; \
				ln -s $(UI_NEXT_LOCAL) $(UI_NEXT_DIR)/src; \
			fi; \
		else \
			echo "=== Linking $(UI_NEXT_DIR)/src to $(UI_NEXT_LOCAL) ==="; \
			ln -s $(UI_NEXT_LOCAL) $(UI_NEXT_DIR)/src; \
		fi; \
	elif [ ! -z "$(UI_NEXT_GIT_REPO)" ]; then \
		if [ -d $(UI_NEXT_DIR)/src ]; then \
			GIT_REMOTE_ORIGIN=$$(cd $(UI_NEXT_DIR)/src && git remote get-url origin); \
			GIT_REMOTE_BRANCH=$$(cd $(UI_NEXT_DIR)/src && git rev-parse --abbrev-ref HEAD); \
			if [ "$$GIT_REMOTE_ORIGIN" = "$(UI_NEXT_GIT_REPO)" ] && [ "$$GIT_REMOTE_BRANCH" = "$(UI_NEXT_GIT_BRANCH)" ]; then \
				echo "=== Updating $(UI_NEXT_DIR)/src from $(UI_NEXT_GIT_BRANCH) of $(UI_NEXT_GIT_REPO) ==="; \
				git fetch && git pull; \
			else \
				echo "=== Cloning $(UI_NEXT_DIR)/src from $(UI_NEXT_GIT_BRANCH) of $(UI_NEXT_GIT_REPO) ==="; \
				rm -rf $(UI_NEXT_DIR)/src; \
				git clone --depth 1 --branch $(UI_NEXT_GIT_BRANCH) $(UI_NEXT_GIT_REPO) $(UI_NEXT_DIR)/src || true; \
			fi; \
		else \
			echo "=== Cloning $(UI_NEXT_DIR)/src from $(UI_NEXT_GIT_BRANCH) of $(UI_NEXT_GIT_REPO) ==="; \
			git clone --depth 1 --branch $(UI_NEXT_GIT_BRANCH) $(UI_NEXT_GIT_REPO) $(UI_NEXT_DIR)/src || true; \
		fi; \
	else \
		echo "FAILED: ui-next/src. UI_NEXT_LOCAL and UI_NEXT_GIT_REPO are not set."; \
		exit 1; \
	fi

.PHONY: ui-next/src/webpack
## Install webpack.
ui-next/src/webpack: $(UI_NEXT_DIR)/src/node_modules/webpack

.PHONY: $(UI_NEXT_DIR)/src/node_modules/webpack
## True target for ui-next/src/webpack.
$(UI_NEXT_DIR)/src/node_modules/webpack:
	@echo "=== Installing webpack ==="
	@cd $(UI_NEXT_DIR)/src && npm install webpack

.PHONY: clean/ui-next
## Clean ui_next
clean/ui-next: clean/ui-next/build clean/ui-next/src

.PHONY: clean/ui-next/src
## Clean ui_next src
clean/ui-next/src:
	rm -rf $(UI_NEXT_DIR)/src

.PHONY: clean/ui-next/build
## Clean ui_next build
clean/ui-next/build:
	rm -rf $(UI_NEXT_DIR)/build
