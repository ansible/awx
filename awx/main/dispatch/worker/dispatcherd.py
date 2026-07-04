from typing import Any

from dispatcherd.worker.task import TaskWorker
from django.db import connection
from opentelemetry.trace import get_tracer, Status, StatusCode
from ansible_base.observability import setup_observability


tracer = get_tracer(__name__)


class AWXTaskWorker(TaskWorker):

    def on_start(self) -> None:
        """
        Initialize worker process: database connection and observability.
        Called once per worker process after fork.
        """
        # Initialize OpenTelemetry in this worker process
        setup_observability(service_name="aap-controller-dispatcher")

        # Get worker connected so that first task it gets will be worked quickly
        connection.ensure_connection()

    def pre_task(self, message) -> None:
        """This should remedy bad connections that can not fix themselves"""
        connection.close_if_unusable_or_obsolete()

    def run_callable(self, message: dict) -> Any:
        """
        Import and execute a task with OpenTelemetry instrumentation.
        Wraps task execution in a span with rich attributes.
        """
        task = message['task']
        uuid = self.get_uuid(message)
        args = message.get('args', [])
        kwargs = message.get('kwargs', {})

        # Extract task name components for span naming
        # task = "awx.main.tasks.system.apply_cluster_membership_policies"
        # Handle edge cases like lambda tasks or tasks without module paths
        if '.' in task:
            task_module, task_function = task.rsplit('.', 1)
        else:
            task_module = ""
            task_function = task

        # Normalize lambda broker tasks to stable name
        # task = 'lambda: "broker_a89d6bc1_506a_4f37_8ce2_475f1291cc2c"' -> "broker_task"
        if task_function.startswith('lambda:') and 'broker_' in task_function:
            task_function = "broker_task"

        # Create span with task function name (like HTTP route)
        with tracer.start_as_current_span(task_function) as span:
            # Set rich span attributes
            span.set_attribute("task.name", task)
            span.set_attribute("task.uuid", uuid)
            span.set_attribute("task.module", task_module)
            span.set_attribute("task.function", task_function)
            span.set_attribute("task.args_count", len(args))
            span.set_attribute("task.kwargs_count", len(kwargs))
            span.set_attribute("task.worker_id", self.worker_id)

            # Add correlation ID if available (from guid in message body)
            if 'guid' in message:
                span.set_attribute("correlation_id", message['guid'])

            try:
                # Call parent class implementation
                result = super().run_callable(message)

                # Mark span as successful
                span.set_status(Status(StatusCode.OK))
                return result

            except Exception as e:
                # Record exception in span
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.set_attribute("task.error_type", type(e).__name__)
                span.set_attribute("task.error_message", str(e))
                span.record_exception(e)
                raise
