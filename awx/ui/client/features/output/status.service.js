const JOB_START = 'playbook_on_start';
const JOB_END = 'playbook_on_stats';
const PLAY_START = 'playbook_on_play_start';
const TASK_START = 'playbook_on_task_start';

const HOST_STATUS_KEYS = ['dark', 'failures', 'changed', 'ok', 'skipped'];
const FINISHED = ['successful', 'failed', 'error'];

function JobStatusService (moment, message) {
    this.dispatch = () => message.dispatch('status', this.state);
    this.subscribe = listener => message.subscribe('status', listener);

    this.init = ({ resource }) => {
        const { model } = resource;

        this.created = model.get('created');
        this.job = model.get('id');
        this.jobType = model.get('type');
        this.project = model.get('project');

        this.active = false;
        this.latestTime = null;
        this.counter = -1;

        this.state = {
            running: false,
            stats: false,
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

        this.setStatsEvent(resource.stats);
        this.updateStats();
        this.updateRunningState();

        this.dispatch();
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
        (this.jobType === 'project_update');

    this.updateStats = () => {
        this.updateHostCounts();

        if (this.statsEvent) {
            this.state.stats = true;
            this.setFinished(this.statsEvent.created);
            this.setJobStatus(this.statsEvent.failed ? 'failed' : 'successful');
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
        this.state.status = status;

        if (!this.isExpectingStatsEvent() && _.includes(FINISHED, status)) {
            if (this.latestTime) {
                this.setFinished(this.latestTime);
                if (!this.state.started && this.state.elapsed) {
                    this.setStarted(moment(this.latestTime)
                        .subtract(this.state.elapsed, 'seconds'));
                }
            }
        }

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
        this.state.hosts = counts;
    };

    this.resetCounts = () => {
        this.state.counts.plays = 0;
        this.state.counts.tasks = 0;
        this.state.counts.hosts = 0;
    };
}

JobStatusService.$inject = [
    'moment',
    'JobMessageService',
];

export default JobStatusService;
