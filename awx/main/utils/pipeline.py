import datetime
import json
import socket
import binascii
from awx.main.utils.handlers import RSysLogHandler
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder


class RSysLog():
    def __init__(self, address=settings.LOGGING['handlers']['external_logger']['address']):
        self.address = address
        self.socktype = socket.SOCK_DGRAM

        if isinstance(address, str):
            self.unixsocket = True
            # Syslog server may be unavailable during handler initialisation.
            # C's openlog() function also ignores connection errors.
            # Moreover, we ignore these errors while logging, so it not worse
            # to ignore it also here.
            try:
                self._connect_unixsocket(address)
            except OSError:
                pass

    def _connect_unixsocket(self, address):
        self.socket = socket.socket(socket.AF_UNIX, self.socktype)
        try:
            self.socket.connect(address)
            self.socket.setblocking(False)
        except OSError:
            self.socket.close()
            raise

    def emit(self, msg):
        msg = json.dumps(msg, cls=DjangoJSONEncoder)
        try:
            msg += '\000'
            # Message is a string. Convert to bytes as required by RFC 5424
            msg = msg.encode('utf-8')
            try:
                self.socket.send(msg)
            except OSError:
                self.socket.close()
                self._connect_unixsocket(self.address)
                self.socket.send(msg)
        except Exception:
            raise

glob_logger = None


def emit(msg):
    global glob_logger
    if not glob_logger:
        glob_logger = RSysLog()
    glob_logger.emit(msg)


class PipelineJobBase():
    pipeline = ''
    step = ''

    @classmethod
    def create_msg(cls, step, job_id, ts=None):
        if not ts:
            ts = datetime.datetime.now()

        pipeline_step_fq = f"{cls.pipeline}.{step}"

        step_index = cls.steps.index(step)

        msg = {
            '@timestamp': ts,
            'correlation_id': f"{hash(pipeline_step_fq)}{job_id}",
            'message': 'blah',
            'pipeline': cls.pipeline,
            'step': step,
            'pipeline_step': pipeline_step_fq,
            'job_id': job_id,
            'group_id': cls.step_order_ids[step_index][0],
            'step_id': cls.step_order_ids[step_index][1],
            'group_step_id': float(f"{cls.step_order_ids[step_index][0]}.{cls.step_order_ids[step_index][1]}")
        }
        '''
        step = 'task_manager.start'
        msg['group0'] = 'task_manager'
        msg['group1'] = 'start'
        '''
        for i, group in enumerate(step.split('.')):
            msg[f'group{i}'] = group
        print(msg)
        return msg

    @classmethod
    def start(cls, step, job_id, ts=None):
        if step not in cls.steps:
            raise ValueError(f'Pipeline step "{self.step}" not found in steps "{self.steps}"')
        msg = cls.create_msg(step, job_id, ts)
        msg['start'] = msg['@timestamp']
        emit(msg)

    @classmethod
    def end(cls, job_id, ts=None):
        msg = cls.create_msg(job_id, ts)
        msg['end'] = msg['@timestamp']
        emit(msg)


class PipelineJob(PipelineJobBase):
    pipeline = 'job'
    pipeline_id = 1
    steps = [
        'api.job_create',
        'task_manager.start_task',
        'dispatcher.apply_async',
        'run_job.run_before',
        'run_job.run_during',
        'run_job.run_after',
    ]
    step_order_ids = []

def init():
    group_count = 0
    step_count = 0
    current_group = None
    for step_fq in PipelineJob.steps:
        group, step = step_fq.split('.')
        if current_group != group:
            current_group = group
            group_count += 1
            step_count = 0
        step_count += 1
        PipelineJob.step_order_ids.append((group_count, step_count))

init()
