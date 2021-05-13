if [ -z $AWX_IGNORE_BLACK ]
then
        black --check $(git diff --cached --name-only --diff-filter=AM | grep -E '\.py') || \
        (echo 'To fix this, run `make black` to auto-format your code prior to commit, or set AWX_IGNORE_BLACK=1' && \
        exit 1)
fi
