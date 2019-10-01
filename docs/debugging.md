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

Whitelist this IP address by adding it to the `INTERNAL_IPS` variable in `local_settings`, then navigate to the API and you should see DDT on the
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
