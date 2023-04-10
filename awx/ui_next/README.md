# Instruction to build ui_next directly from this directory

## Set src of the ui_next repo

### Via GIT

```bash
export UI_NEXT_GIT_REPO=https://<git repo>
```

or

```bash
export UI_NEXT_GIT_REPO=git@<git repo>
```

optionally set branch (default is main)

```bash
export UI_NEXT_GIT_BRANCH=main
```

### Via symlink to existing clone

NOTE: UI_NEXT_LOCAL have higher precedence than UI_NEXT_GIT_REPO, if UI_NEXT_LOCAL is set, UI_NEXT_GIT_REPO will be ignored.

```bash
export UI_NEXT_LOCAL = /path/to/your/ui_next
```

## Build

```bash
make ui-next
```

## Rebuild

```bash
make -B ui-next
```

## Clean

```bash
make clean/ui-next
```
