# Copyright (c) 2018 Ansible by Red Hat
# All Rights Reserved.

import six


class _AwxTaskError():
    def build_exception(self, task, message=None):
        if message is None:
            message = six.text_type("Execution error running {}").format(task.log_format)
        e = Exception(message)
        e.task = task
        e.is_awx_task_error = True
        return e

    def TaskCancel(self, task, rc):
        """Canceled flag caused run_pexpect to kill the job run"""
        message=six.text_type("{} was canceled (rc={})").format(task.log_format, rc)
        e = self.build_exception(task, message)
        e.rc = rc
        e.awx_task_error_type = "TaskCancel"
        return e

    def TaskError(self, task, rc):
        """Userspace error (non-zero exit code) in run_pexpect subprocess"""
        message = six.text_type("{} encountered an error (rc={}), please see task stdout for details.").format(task.log_format, rc)
        e = self.build_exception(task, message)
        e.rc = rc
        e.awx_task_error_type = "TaskError"
        return e


AwxTaskError = _AwxTaskError()
