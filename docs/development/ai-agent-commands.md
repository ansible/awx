# AI Agent Command Permissions

This document defines which commands AI agents (Claude, etc.) may run automatically without asking
for confirmation, and which require explicit user approval.

---

## Commands That May Run Without Confirmation

### Testing

Unit and functional tests use SQLite and run directly from the repo root — no containers needed:

```bash
make test
make test_unit
make test_coverage
make test_migrations
py.test awx/main/tests/unit/
py.test awx/main/tests/functional/
py.test awx/conf/tests/
py.test awx/main/tests/unit/path/to/test_something.py::TestClass::test_method
```

Live tests require `make docker-compose` to be running and **must** be run inside the container:

```bash
docker exec tools_awx_1 bash -c "cd /awx && py.test awx/main/tests/live/"
```

### Code Quality

```bash
make check
make black
flake8
tox -e linters
```

### Read-Only Git Operations

```bash
git status
git diff
git log
git show
git fetch
git branch
```

### Read-Only Container / Django Inspection

```bash
docker ps
docker logs tools_awx_1
docker exec tools_awx_1 awx-manage check
docker exec tools_awx_1 awx-manage diffsettings
docker exec tools_awx_1 awx-manage showmigrations
```

### Dependency / Environment Inspection

```bash
pip list
pip show <package>
python -m pip check
```

---

## Commands That Require Explicit User Confirmation

These commands are destructive, affect shared state, or are hard to reverse.

### Git — Destructive or Remote

```bash
git push                  # pushes to shared remote
git push --force          # overwrites remote history
git reset --hard          # discards all local changes
git restore .             # discards working-tree changes
git restore <file>        # discards changes to a specific file
git checkout -- <file>    # discards changes (old syntax)
git clean -f / -fd        # deletes untracked files/dirs
git commit                # creates a commit (user should review first)
```

### GitHub CLI — Visible to Others

```bash
gh pr create
gh pr merge
gh pr close
gh pr comment
gh pr review
gh issue create
gh issue close
gh issue comment
gh release create
```

### Any Other Potentially Destructive Command

When in doubt, ask. The general rule: if a command **cannot be undone without extra effort** or
**affects something outside the local working tree**, confirm with the user first.
