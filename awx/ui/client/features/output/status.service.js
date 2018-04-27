const JOB_START = 'playbook_on_start';
const JOB_END = 'playbook_on_stats';
const PLAY_START = 'playbook_on_play_start';
const TASK_START = 'playbook_on_task_start';

const HOST_STATUS_KEYS = ['dark', 'failures', 'changed', 'ok', 'skipped'];
const FINISHED = ['successful', 'failed', 'error'];

let moment;

function JobStatusService (_moment_) {
    moment = _moment_;

    this.init = ({ resource }) => {
        this.counter = -1;

        this.created = resource.model.get('created');
        this.job = resource.model.get('id');
        this.jobType = resource.model.get('type');
        this.project = resource.model.get('project');
        this.elapsed = resource.model.get('elapsed');
        this.started = resource.model.get('started');
        this.finished = resource.model.get('finished');
        this.jobStatus = resource.model.get('status');
        this.projectStatus = resource.model.get('summary_fields.project_update.status');
        this.projectUpdateId = resource.model.get('summary_fields.project_update.id');

        this.latestTime = null;
        this.playCount = null;
        this.taskCount = null;
        this.hostCount = null;
        this.active = false;
        this.hostStatusCounts = {};

        this.statsEvent = resource.stats;
        this.updateStats();
    };

    this.pushStatusEvent = data => {
        const isJobEvent = (this.job === data.unified_job_id);
        const isProjectEvent = (this.project && (this.project === data.project_id));

        if (isJobEvent) {
            this.setJobStatus(data.status);
        } else if (isProjectEvent) {
            this.setProjectStatus(data.status);
            this.setProjectUpdateId(data.unified_job_id);
        }
    };

    this.pushJobEvent = data => {
        const isLatest = ((!this.counter) || (data.counter > this.counter));

        if (!this.active && !(data.event === JOB_END)) {
            this.active = true;
            this.setJobStatus('running');
        }

        if (isLatest) {
            this.counter = data.counter;
            this.latestTime = data.created;
            this.elapsed = moment(data.created).diff(this.created, 'seconds');
        }

        if (data.event === JOB_START) {
            this.started = this.started || data.created;
        }

        if (data.event === PLAY_START) {
            this.playCount++;
        }

        if (data.event === TASK_START) {
            this.taskCount++;
        }

        if (data.event === JOB_END) {
            this.statsEvent = data;
        }
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

        this.hostCount = countedHostNames.length;
        this.hostStatusCounts = counts;
    };

    this.updateStats = () => {
        this.updateHostCounts();

        if (this.statsEvent) {
            this.setFinished(this.statsEvent.created);
            this.setJobStatus(this.statsEvent.failed ? 'failed' : 'successful');
        }
    };

    this.isRunning = () => (Boolean(this.started) && !this.finished) ||
        (this.jobStatus === 'running') ||
        (this.jobStatus === 'pending') ||
        (this.jobStatus === 'waiting');

    this.isExpectingStatsEvent = () => (this.jobType === 'job') ||
        (this.jobType === 'project_update');

    this.getPlayCount = () => this.playCount;
    this.getTaskCount = () => this.taskCount;
    this.getHostCount = () => this.hostCount;
    this.getHostStatusCounts = () => this.hostStatusCounts || {};
    this.getJobStatus = () => this.jobStatus;
    this.getProjectStatus = () => this.projectStatus;
    this.getProjectUpdateId = () => this.projectUpdateId;
    this.getElapsed = () => this.elapsed;
    this.getStatsEvent = () => this.statsEvent;
    this.getStarted = () => this.started;
    this.getFinished = () => this.finished;

    this.setJobStatus = status => {
        this.jobStatus = status;

        if (!this.isExpectingStatsEvent() && _.includes(FINISHED, status)) {
            if (this.latestTime) {
                this.setFinished(this.latestTime);

                if (!this.started && this.elapsed) {
                    this.started = moment(this.latestTime).subtract(this.elapsed, 'seconds');
                }
            }
        }
    };

    this.setProjectStatus = status => {
        this.projectStatus = status;
    };

    this.setProjectUpdateId = id => {
        this.projectUpdateId = id;
    };

    this.setFinished = time => {
        this.finished = time;
    };

    this.resetCounts = () => {
        this.playCount = 0;
        this.taskCount = 0;
        this.hostCount = 0;
    };
}

JobStatusService.$inject = [
    'moment',
];

export default JobStatusService;
