Debugging
=========

Django Debug Toolbar (DDT)
----------------
This is a useful tool for examining SQL queries, performance, headers, requests, signals, cache, logging, and more.  

To enable DDT, you need to set your `INTERNAL_IPS` to the IP address of your load balancer.  This can be overriden in `local_settings`.  
This IP address can be found by making a GET to any page on the browsable API and looking for a like this in the standard output:
```
awx_1        | 14:42:08 uwsgi.1     | 172.18.0.1 GET /api/v2/tokens/ - HTTP/1.1 200
```

Allow this IP address by adding it to the `INTERNAL_IPS` variable in `local_settings`, then navigate to the API and you should see DDT on the
right side.  If you don't see it, make sure to set `DEBUG=True`.  
> Note that enabling DDT is detrimental to the performance of AWX and adds overhead to every API request.  It is
recommended to keep this turned off when you are not using it.  

SQL Debugging
-------------
AWX includes a powerful tool for tracking slow queries across all of its Python processes.
As the AWX user, run:

```
$ awx-manage profile_sql --threshold 2 --minutes 5
```

...where threshold is the max query time in seconds, and minutes it the number of minutes to record.
For the next five minutes (in this example), any AWX Python process that generates a SQL query
that runs for >2s will be recorded in a `.sqlite` database in `/var/log/tower/profile`.

This is a useful tool for logging all queries at a per-process level, or filtering and searching for
queries within a certain code branch.  For example, if you observed that certain HTTP requests were
particularly slow, you could enable profiling, perform the slow request, and then search the log:

```
$ sqlite3 -column -header /var/log/tower/profile/uwsgi.sqlite
sqlite> .schema queries
CREATE TABLE queries (
    id INTEGER PRIMARY KEY,
    version TEXT,             # the AWX version
    pid INTEGER,              # the pid of the process
    stamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    argv REAL,                # argv of the process
    time REAL,                # time to run the query (in seconds)
    sql TEXT,                 # the actual query
    explain TEXT,             # EXPLAIN VERBOSE ... of the query
    bt TEXT                   # python stack trace that led to the query running
);
sqlite> SELECT time, sql FROM queries ORDER BY time DESC LIMIT 1;
time        sql
----------  ---------------------------------------------------------------------------------------------
0.046       UPDATE "django_session" SET "session_data" = 'XYZ', "expire_date" = '2019-02-15T21:56:45.693290+00:00'::timestamptz WHERE "django_session"."session_key" = 'we9dumywgju4fulaxz3oki58zpxgmd6t'
```

Remote Debugging
----------------
Python processes in Tower's development environment are kept running in the
background via supervisord.  As such, interacting with them via Python's
standard `pdb.set_trace()` isn't possible.

Bundled in our container environment is a remote debugging tool, `sdb`.  You
can use it to set remote breakpoints in Tower code and debug interactively over
a telnet session:

```python
    # awx/main/tasks.py

    class SomeTask(awx.main.tasks.BaseTask):

        def run(self, pk, **kwargs):
            # This will set a breakpoint and open an interactive Python
            # debugger exposed on a random port between 7899-7999.  The chosen
            # port will be reported as a warning in the Tower logs, e.g.,
            #
            # [2017-01-30 22:26:04,366: WARNING/Worker-11] Remote Debugger:7900: Please telnet into 0.0.0.0 7900.
            #
            # You can access it from your host machine using telnet:
            #
            # $ telnet localhost <port>
            import sdb
            sdb.set_trace()
```

Keep in mind that when you interactively debug in this way, any process
that encounters a breakpoint will wait until an active client is established
(it won't handle additional tasks) and concludes the debugging session with
a `continue` command.

To simplify remote debugging session management, Tower's development
environment comes with tooling that can automatically discover open
remote debugging sessions and automatically connect to them.  From your *host*
machine (*i.e.*, _outside_ of the development container), you can run:

```
sdb-listen
```

This will open a Python process that listens for new debugger sessions and
automatically connects to them for you.

Graph Jobs
----------
The `awx-manage graph_jobs` can be used to visualize how Jobs progress from
pending to waiting to running.

```
awx-manage graph_jobs --help
usage: awx-manage graph_jobs [-h] [--refresh REFRESH] [--width WIDTH]
                             [--height HEIGHT] [--version] [-v {0,1,2,3}]
                             [--settings SETTINGS] [--pythonpath PYTHONPATH]
                             [--traceback] [--no-color] [--force-color]

Plot pending, waiting, running jobs over time on the terminal

optional arguments:
  -h, --help            show this help message and exit
  --refresh REFRESH     Time between refreshes of the graph and data in
                        seconds (defaults to 1.0)
  --width WIDTH         Width of the graph (defaults to 100)
  --height HEIGHT       Height of the graph (defaults to 30)
```

Below is an example run with 200 Jobs flowing through the system.

[![asciicast](https://asciinema.org/a/xnfzMQ30xWPdhwORiISz0wcEw.svg)](https://asciinema.org/a/xnfzMQ30xWPdhwORiISz0wcEw)
=======
Code Instrumentation Profiling
------------------------------
Decorate a function to generate profiling data that will tell you the percentage
of time spent in branches of a code path. This comes at an absolute performance
cost. However, the relative numbers are still very helpful.

Requirements for `dot_enabled=True`
**Note:** The profiling code will run as if `dot_enabled=False` when `gprof2dot`
package is not found
```
/var/lib/awx/venv/awx/bin/pip3 install gprof2dot
```

Below is the signature of the `@profile` decorator.
```
@profile(name, dest='/var/log/tower/profile', dot_enabled=True)
```

```
from awx.main.utils.profiling import profile

@profile(name="task_manager_profile")
def task_manager():
    ...
```

Now, invoke the function being profiled. Each run of the profiled function
will result in a file output to `dest` containing the profile data summary as
well as a dot graph if enabled. The profile data summary can be viewed in a
text editor. The dot graph can be viewed using `xdot`.

```
bash-4.4$ ls -aln /var/log/tower/profile/
total 24
drwxr-xr-x 2 awx  root 4096 Oct 15 13:23 .
drwxrwxr-x 1 root root 4096 Oct 15 13:23 ..
-rw-r--r-- 1 awx  root  635 Oct 15 13:23 2.001s-task_manager_profile-2303-272858af-3bda-45ec-af9e-7067aa86e4f3.dot
-rw-r--r-- 1 awx  root  587 Oct 15 13:23 2.001s-task_manager_profile-2303-272858af-3bda-45ec-af9e-7067aa86e4f3.pstats
-rw-r--r-- 1 awx  root  632 Oct 15 13:23 2.002s-task_manager_profile-2303-4cdf4660-3ef4-4238-8164-33611822d9e3.dot
-rw-r--r-- 1 awx  root  587 Oct 15 13:23 2.002s-task_manager_profile-2303-4cdf4660-3ef4-4238-8164-33611822d9e3.pstats
```

```
xdot /var/log/tower/profile/2.001s-task_manager_profile-2303-272858af-3bda-45ec-af9e-7067aa86e4f3.dot
```


Code Instrumentation Timing
---------------------------
Similar to the profiling decorator, there is a timing decorator. This is useful
when you do not want to incur the overhead of profiling and want to know the
accurate absolute timing of a code path.

Below is the signature of the `@timing` decorator.
```
@timing(name, dest='/var/log/tower/timing')
```

```
from awx.main.utils.profiling import timing

@timing(name="my_task_manager_timing")
def task_manager():
    ...
```

Now, invoke the function being timed. Each run of the timed function will result
in a file output to `dest`. The timing data will be in the file name.

```
bash-4.4# ls -aln
total 16
drwxr-xr-x 2 0 0 4096 Oct 20 12:43 .
drwxrwxr-x 1 0 0 4096 Oct 20 12:43 ..
-rw-r--r-- 1 0 0   61 Oct 20 12:43 2.002178-seconds-my_task_manager-ab720a2f-4624-47d0-b897-8549fe7e8c99.time
-rw-r--r-- 1 0 0   60 Oct 20 12:43 2.00228-seconds-my_task_manager-e8a901be-9cdb-4ffc-a34a-a6bcb4266e7c.time
```

The class behind the decorator can also be used for profiling.

```
from awx.main.utils.profiling import AWXProfiler

prof = AWXProfiler("hello_world")
prof.start()
'''
code to profile here
'''
prof.stop()


# Note that start() and stop() can be reused. An new profile file will be output.
prof.start()
'''
more code to profile
'''
prof.stop()
```
