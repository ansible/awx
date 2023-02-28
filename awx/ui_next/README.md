# Instruction to build ui_next directly from this directory

## Set src of the ui_next repo

### via GIT

```bash
export UI_NEXT_GIT_BRANCH_REPO_HTTPS=https://<git repo>
```

or

```bash
export UI_NEXT_GIT_BRANCH_REPO_SSH=git@<git repo>
```

optionally set branch (default is main)

```bash
export UI_NEXT_GIT_BRANCH_BRANCH=main
```

### via symlink to existing clone

```bash
export UI_NEXT_LOCAL = /path/to/your/ui_next
```

## Build

```bash
make ui_next/build
```
