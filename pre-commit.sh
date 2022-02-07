if [ -z $AWX_IGNORE_BLACK ] ; then
	python_files_changed=$(git diff --cached --name-only --diff-filter=AM | grep -E '\.py')
	if [ "x$python_files_changed" != "x" ] ; then
        	black --check $python_files_changed || \
        	(echo 'To fix this, run `make black` to auto-format your code prior to commit, or set AWX_IGNORE_BLACK=1' && \
        	exit 1)
	fi
fi
