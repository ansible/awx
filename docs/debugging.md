Debugging
=========



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
            # debugger exposed on a random port between 6899-6999.  The chosen
            # port will be reported as a warning in the Tower logs, e.g.,
            #
            # [2017-01-30 22:26:04,366: WARNING/Worker-11] Remote Debugger:6900: Please telnet into 0.0.0.0 6900.
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
machine (i.e., _outside_ of the development container), you can run:

```
sdb-listen
```

This will open a Python process that listens for new debugger sessions and
automatically connects to them for you.
