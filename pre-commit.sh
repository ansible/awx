if [ -z $AWX_IGNORE_BLACK ] ; then
	python_files_changed=$(git diff --cached --name-only --diff-filter=AM | grep -E '\.py')
	if [ "x$python_files_changed" != "x" ] ; then
        	black --check $python_files_changed || \
        	(echo 'To fix this, run `make black` to auto-format your code prior to commit, or set AWX_IGNORE_BLACK=1' && \
        	exit 1)
	fi
fi

if [ -z $AWX_IGNORE_USER ] ; then
	if [ -d ./pre-commit-user ] ; then
		for SCRIPT in `find ./pre-commit-user -name "*.sh" -executable` ; do
			$SCRIPT || exit 1
		done
	fi
fi
