class AwxTaskError(Exception):
    """Base exception for errors in unified job runs"""
    def __init__(self, task, message=None):
        if message is None:
            message = "Execution error running {}".format(task.log_format)
        super(AwxTaskError, self).__init__(message)
        self.task = task
 
 
class TaskCancel(AwxTaskError):
    """Canceled flag caused run_pexpect to kill the job run"""
    def __init__(self, task, rc):
        super(TaskCancel, self).__init__(
            task, message="{} was canceled (rc={})".format(task.log_format, rc))
        self.rc = rc


class TaskError(AwxTaskError):
    """Userspace error (non-zero exit code) in run_pexpect subprocess"""
    def __init__(self, task, rc):
        super(TaskError, self).__init__(
            task, message="%s encountered an error (rc=%s), please see task stdout for details.".format(task.log_format, rc))
        self.rc = rc

