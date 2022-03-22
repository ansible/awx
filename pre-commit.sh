if [ -z $AWX_IGNORE_BLACK ] ; then
	python_files_changed=$(git diff --cached --name-only --diff-filter=AM | grep -E '\.py')
	if [ "x$python_files_changed" != "x" ] ; then
        	black --check $python_files_changed || \
        	(echo 'To fix this, run `make black` to auto-format your code prior to commit, or set AWX_IGNORE_BLACK=1' && \
        	exit 1)
	fi
fi

if [ -z $AWX_IGNORE_USER ] ; then
	FAIL=0
	export CHANGED_FILES=$(git diff --cached --name-only --diff-filter=AM)
	if [ -d ./pre-commit-user ] ; then
		for SCRIPT in `find ./pre-commit-user -executable -type f` ; do
			echo "Running user pre-commit hook $SCRIPT"
			$SCRIPT
			if [ $? != 0 ] ; then
				echo "User test $SCRIPT failed"
			       	FAIL=1
			fi
		done
	fi
	if [ $FAIL == 1 ] ; then
		echo "One or more user tests failed, see messages above"
		exit 1
	fi
fi
