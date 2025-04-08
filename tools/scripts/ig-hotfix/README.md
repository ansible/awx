# Hotfix for Instance Groups and Roles after backup/restore corruption #

## role_check.py ##

`awx-manage shell < role_check.py 2> role_check.log > fix.py`

This checks the roles and resources on the system, and constructs a
fix.py file that will change the linkages of the roles that it finds
are incorrect. The command line above also redirects logging output to
a file. The fix.py file (and the log file) can then be examined (and
potentially modified) before performing the actual fix.

`awx-manage shell < fix.py > fix.log 2>&1`

This performs the fix, while redirecting all output to another log
file. Ideally, this file should wind up being empty after execution
completes.

`awx-manage shell < role_check.py 2> role_check2.log > fix2.py`

Re-run the check script in order to see that there are no remaining
problems. Ideally the log file will only consist of the equal-sign
lines.


## foreignkeys.sql ##

This script uses Postgres internals to determine all of the foreign
keys that cross the boundaries established by our (old) backup/restore
logic.  Users have no need to run this.


## scenarios/test*.py ##

These files were used to set up corruption similar to that caused by
faulty backup/restore, for testing purposes.  Do not use.
