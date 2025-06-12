from dispatcherd.worker.task import TaskWorker

from django.db import connection


class AWXTaskWorker(TaskWorker):

    def on_start(self) -> None:
        """Get worker connected so that first task it gets will be worked quickly"""
        connection.ensure_connection()

    def pre_task(self, message) -> None:
        """This should remedy bad connections that can not fix themselves"""
        connection.close_if_unusable_or_obsolete()
