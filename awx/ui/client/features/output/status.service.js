/* eslint camelcase: 0 */
const JOB_START = 'playbook_on_start';
const JOB_END = 'playbook_on_stats';
const PLAY_START = 'playbook_on_play_start';
const TASK_START = 'playbook_on_task_start';

const HOST_STATUS_KEYS = ['dark', 'failures', 'changed', 'ok', 'skipped'];
const COMPLETE = ['successful', 'failed'];
const INCOMPLETE = ['canceled', 'error'];
const UNSUCCESSFUL = ['failed'].concat(INCOMPLETE);
const FINISHED = COMPLETE.concat(INCOMPLETE);

function JobStatusService (moment, message) {
    this.dispatch = () => message.dispatch('status', this.state);
    this.subscribe = listener => message.subscribe('status', listener);

    this.init = ({ model }) => {
        this.created = model.get('created');
        this.job = model.get('id');
        this.jobType = model.get('type');
        this.project = model.get('project');

        this.active = false;
        this.latestTime = null;
        this.counter = -1;

        this.state = {
            running: false,
            counts: {
                plays: 0,
                tasks: 0,
                hosts: 0,
            },
            hosts: {},
            status: model.get('status'),
            elapsed: model.get('elapsed'),
            started: model.get('started'),
            finished: model.get('finished'),
            scm: {
                id: model.get('summary_fields.project_update.id'),
                status: model.get('summary_fields.project_update.status')
            },
        };

        if (model.has('host_status_counts')) {
            this.setHostStatusCounts(model.get('host_status_counts'));
        } else {
            const hostStatusCounts = this.createHostStatusCounts(this.state.status);

            this.setHostStatusCounts(hostStatusCounts);
        }

        if (model.has('playbook_counts')) {
            this.setPlaybookCounts(model.get('playbook_counts'));
        } else {
            this.setPlaybookCounts({ task_count: 1, play_count: 1 });
        }

        this.updateRunningState();
        this.dispatch();
    };

    this.createHostStatusCounts = status => {
        if (UNSUCCESSFUL.includes(status)) {
            return { failures: 1 };
        }

        if (COMPLETE.includes(status)) {
            return { ok: 1 };
        }

        return null;
    };

    this.pushStatusEvent = data => {
        const isJobStatusEvent = (this.job === data.unified_job_id);
        const isProjectStatusEvent = (this.project && (this.project === data.project_id));

        if (isJobStatusEvent) {
            this.setJobStatus(data.status);
            this.dispatch();
        } else if (isProjectStatusEvent) {
            this.setProjectStatus(data.status);
            this.setProjectUpdateId(data.unified_job_id);
            this.dispatch();
        }
    };

    this.pushJobEvent = data => {
        const isLatest = ((!this.counter) || (data.counter > this.counter));

        let changed = false;

        if (!this.active && !(data.event === JOB_END)) {
            this.active = true;
            this.setJobStatus('running');
            changed = true;
        }

        if (isLatest) {
            this.counter = data.counter;
            this.latestTime = data.created;
            this.setElapsed(moment(data.created).diff(this.created, 'seconds'));
            changed = true;
        }

        if (data.event === JOB_START) {
            this.setStarted(this.state.started || data.created);
            changed = true;
        }

        if (data.event === PLAY_START) {
            this.state.counts.plays++;
            changed = true;
        }

        if (data.event === TASK_START) {
            this.state.counts.tasks++;
            changed = true;
        }

        if (data.event === JOB_END) {
            this.setStatsEvent(data);
            changed = true;
        }

        if (changed) {
            this.dispatch();
        }
    };

    this.isExpectingStatsEvent = () => (this.jobType === 'job') ||
        (this.jobType === 'project_update') ||
        (this.jobType === 'ad_hoc_command');

    this.updateStats = () => {
        this.updateHostCounts();

        if (this.statsEvent) {
            this.setFinished(this.statsEvent.created);

            const failures = _.get(this.statsEvent, ['event_data', 'failures'], {});
            const dark = _.get(this.statsEvent, ['event_data', 'dark'], {});

            if (this.statsEvent.failed ||
                Object.keys(failures).length > 0 ||
                Object.keys(dark).length > 0) {
                this.setJobStatus('failed');
            } else {
                this.setJobStatus('successful');
            }
        }
    };

    this.updateRunningState = () => {
        this.state.running = (Boolean(this.state.started) && !this.state.finished) ||
            (this.state.status === 'running') ||
            (this.state.status === 'pending') ||
            (this.state.status === 'waiting');
    };

    this.updateHostCounts = () => {
        const countedHostNames = [];

        const counts = Object.assign(...HOST_STATUS_KEYS.map(key => ({ [key]: 0 })));

        HOST_STATUS_KEYS.forEach(key => {
            const hostData = _.get(this.statsEvent, ['event_data', key], {});

            Object.keys(hostData).forEach(hostName => {
                const isAlreadyCounted = (countedHostNames.indexOf(hostName) > -1);
                const shouldBeCounted = ((!isAlreadyCounted) && hostData[hostName] > 0);

                if (shouldBeCounted) {
                    countedHostNames.push(hostName);
                    counts[key]++;
                }
            });
        });

        this.state.counts.hosts = countedHostNames.length;
        this.setHostStatusCounts(counts);
    };

    this.setJobStatus = status => {
        const isExpectingStats = this.isExpectingStatsEvent();
        const isIncomplete = INCOMPLETE.includes(status);
        const isFinished = FINISHED.includes(status);
        const isAlreadyFinished = FINISHED.includes(this.state.status);

        if (isAlreadyFinished) {
            return;
        }

        if ((isExpectingStats && isIncomplete) || (!isExpectingStats && isFinished)) {
            if (this.latestTime) {
                this.setFinished(this.latestTime);
                if (!this.state.started && this.state.elapsed) {
                    this.setStarted(moment(this.latestTime)
                        .subtract(this.state.elapsed, 'seconds'));
                }
            }
        }

        this.state.status = status;
        this.updateRunningState();
    };

    this.setElapsed = elapsed => {
        this.state.elapsed = elapsed;
    };

    this.setStarted = started => {
        this.state.started = started;
        this.updateRunningState();
    };

    this.setProjectStatus = status => {
        this.state.scm.status = status;
    };

    this.setProjectUpdateId = id => {
        this.state.scm.id = id;
    };

    this.setFinished = time => {
        this.state.finished = time;
        this.updateRunningState();
    };

    this.setStatsEvent = data => {
        this.statsEvent = data;
    };

    this.setHostStatusCounts = counts => {
        counts = counts || {};

        HOST_STATUS_KEYS.forEach(key => {
            counts[key] = counts[key] || 0;
        });

        if (!this.state.counts.hosts) {
            this.state.counts.hosts = Object.keys(counts)
                .reduce((sum, key) => sum + counts[key], 0);
        }

        this.state.hosts = counts;
    };

    this.setPlaybookCounts = ({ play_count, task_count }) => {
        this.state.counts.plays = play_count;
        this.state.counts.tasks = task_count;
    };

    this.resetCounts = () => {
        this.state.counts.plays = 0;
        this.state.counts.tasks = 0;
        this.state.counts.hosts = 0;
    };
}

JobStatusService.$inject = [
    'moment',
    'OutputMessageService',
];

export default JobStatusService;
