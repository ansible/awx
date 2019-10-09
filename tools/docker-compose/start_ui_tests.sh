#!/bin/bash
set +x

PR_BRANCH=$(git branch | grep \* | cut -d ' ' -f2)

CHANGED_UI_NEXT_FILES=$(git diff --name-only ${PR_BRANCH} devel | grep awx\/ui_next)
CHANGED_UI_FILES=$(git diff --name-only ${PR_BRANCH} devel | grep awx\/ui | grep -v next)

echo $CHANGED_UI_FILES
if [ -n "$CHANGED_UI_FILES" ]
then
  make ui-zuul-lint-and-test
fi

echo $CHANGED_UI_NEXT_FILES
if [ -n "$CHANGED_UI_NEXT_FILES" ]
then
  make ui-next-zuul-lint-and-test
fi
