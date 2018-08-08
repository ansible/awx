import multiprocessing
import random
import sys
from uuid import uuid4

import pytest

from awx.main.dispatch.worker import BaseWorker
from awx.main.dispatch.pool import WorkerPool


class SimpleWorker(BaseWorker):

    def perform_work(self, body, *args):
        pass


class ResultWriter(BaseWorker):

    def perform_work(self, body, result_queue):
        result_queue.put(body + '!!!')


@pytest.mark.django_db
class TestWorkerPool:

    def setup_method(self, test_method):
        self.pool = WorkerPool(min_workers=3)

    def teardown_method(self, test_method):
        self.pool.stop()

    def test_worker(self):
        self.pool.init_workers(SimpleWorker().work_loop)
        assert len(self.pool) == 3
        for worker in self.pool.workers:
            total, _, process = worker
            assert total == 0
            assert process.is_alive() is True

    def test_single_task(self):
        self.pool.init_workers(SimpleWorker().work_loop)
        self.pool.write(0, 'xyz')
        assert self.pool.workers[0][0] == 1  # worker at index 0 handled one task
        assert self.pool.workers[1][0] == 0
        assert self.pool.workers[2][0] == 0

    def test_queue_preference(self):
        self.pool.init_workers(SimpleWorker().work_loop)
        self.pool.write(2, 'xyz')
        assert self.pool.workers[0][0] == 0
        assert self.pool.workers[1][0] == 0
        assert self.pool.workers[2][0] == 1  # worker at index 2 handled one task

    def test_worker_processing(self):
        result_queue = multiprocessing.Queue()
        self.pool.init_workers(ResultWriter().work_loop, result_queue)
        uuids = []
        for i in range(10):
            self.pool.write(
                random.choice(self.pool.workers)[0],
                'Hello, Worker {}'.format(i)
            )
        all_messages = [result_queue.get(timeout=1) for i in range(10)]
        all_messages.sort()
        assert all_messages == [
            'Hello, Worker {}!!!'.format(i)
            for i in range(10)
        ]

        total_handled = sum([worker[0] for worker in self.pool.workers])
        assert total_handled == 10
