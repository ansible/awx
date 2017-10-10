'use strict';

describe('jobResultsService', () => {
    let jobResultsService;

    beforeEach(angular.mock.module('awApp'));

    beforeEach(angular.mock.inject(( _jobResultsService_) => {
        jobResultsService = _jobResultsService_;
    }));

    describe('getCountsFromStatsEvent()', () => {
        it('properly counts hosts based on task state', () => {
            let event_data = {
                "skipped": {
                    "skipped-host": 5  // this host skipped all 5 tasks
                },
                "ok": {
                    "ok-host": 5,  // this host was ok on all 5 tasks
                    "changed-host": 4  // this host had 4 ok tasks, had 1 changed task
                },
                "changed": {
                    "changed-host": 1
                },
                "failures": {
                    "failed-host": 1  // this host had a failed task
                },
                "dark": {
                    "unreachable-host": 1  // this host was unreachable
                },
                "processed": {
                    "ok-host": 1,
                    "changed-host": 1,
                    "skipped-host": 1,
                    "failed-host": 1,
                    "unreachable-host": 1
                },
                "playbook_uuid": "c23d8872-c92a-4e96-9f78-abe6fef38f33",
                "playbook": "some_playbook.yml",
            };
            expect(jobResultsService.getCountsFromStatsEvent(event_data)).toEqual({
                'ok': 1,
                'skipped': 1,
                'unreachable': 1,
                'failures': 1,
                'changed': 1
            });
        });
    });
});
