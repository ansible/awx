# Instruction to build ui directly from this directory

## Set src of the ui repo

### Via GIT

```bash
export UI_GIT_REPO=https://<git repo>
```

or

```bash
export UI_GIT_REPO=git@<git repo>
```

optionally set branch (default is main)

```bash
export UI_GIT_BRANCH=main
```

### Via symlink to existing clone

NOTE: UI_LOCAL have higher precedence than UI_GIT_REPO, if UI_LOCAL is set, UI_GIT_REPO will be ignored.

```bash
export UI_LOCAL = /path/to/your/ui
```

## Build

```bash
make ui
```

## Rebuild

```bash
make -B ui
```

## Clean

```bash
make clean/ui
```
