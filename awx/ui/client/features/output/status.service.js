/* eslint camelcase: 0 */
import {
    EVENT_START_PLAYBOOK,
    EVENT_STATS_PLAY,
    EVENT_START_PLAY,
    EVENT_START_TASK,
    HOST_STATUS_KEYS,
    JOB_STATUS_COMPLETE,
    JOB_STATUS_INCOMPLETE,
    JOB_STATUS_UNSUCCESSFUL,
    JOB_STATUS_FINISHED,
} from './constants';

function JobStatusService (moment, message) {
    this.dispatch = () => message.dispatch('status', this.state);
    this.subscribe = listener => message.subscribe('status', listener);

    this.init = ({ model }) => {
        this.model = model;
        this.created = model.get('created');
        this.job = model.get('id');
        this.jobType = model.get('type');
        this.project = model.get('project');

        this.active = false;
        this.latestTime = null;
        this.counter = -1;

        this.state = {
            running: false,
            anyFailed: false,
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
            environment: model.get('custom_virtualenv'),
            artifacts: model.get('artifacts'),
            scm: {
                id: model.get('summary_fields.project_update.id'),
                status: model.get('summary_fields.project_update.status')
            },
            scmBranch: model.get('scm_branch'),
            scmRefspec: model.get('scm_refspec'),
            inventoryScm: {
                id: model.get('source_project_update'),
                status: model.get('summary_fields.inventory_source.status')
            },
            event_processing_finished: model.get('event_processing_finished'),
        };

        this.initHostStatusCounts({ model });
        this.initPlaybookCounts({ model });

        this.updateRunningState();
        this.dispatch();
    };

    this.initHostStatusCounts = ({ model }) => {
        if (model.has('host_status_counts')) {
            this.setHostStatusCounts(model.get('host_status_counts'));
        } else {
            const hostStatusCounts = this.createHostStatusCounts(this.state.status);

            this.setHostStatusCounts(hostStatusCounts);
        }
    };

    this.initPlaybookCounts = ({ model }) => {
        if (model.has('playbook_counts')) {
            this.setPlaybookCounts(model.get('playbook_counts'));
        } else {
            this.setPlaybookCounts({ task_count: 1, play_count: 1 });
        }
    };

    this.createHostStatusCounts = status => {
        if (JOB_STATUS_UNSUCCESSFUL.includes(status)) {
            return { failures: 1 };
        }

        if (JOB_STATUS_COMPLETE.includes(status)) {
            return { ok: 1 };
        }

        return null;
    };

    this.pushStatusEvent = data => {
        const isJobStatusEvent = (this.job === data.unified_job_id);
        const isProjectStatusEvent = (this.project && (this.project === data.project_id));
        const isInventoryScmStatus = (this.model.get('source_project_update') === data.unified_job_id);

        if (isJobStatusEvent) {
            this.setJobStatus(data.status);
            if (JOB_STATUS_FINISHED.includes(data.status)) {
                this.sync();
            }
            this.dispatch();
        } else if (isProjectStatusEvent) {
            this.setProjectStatus(data.status);
            this.setProjectUpdateId(data.unified_job_id);
            this.dispatch();
        } else if (isInventoryScmStatus) {
            this.setInventoryScmStatus(data.status);
            this.setInventoryScmId(data.unified_job_id);
            this.dispatch();
        }
    };

    this.pushJobEvent = data => {
        const isLatest = ((!this.counter) || (data.counter > this.counter));

        let changed = false;

        if (!this.active && !(data.event === EVENT_STATS_PLAY)) {
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

        if (data.event === EVENT_START_PLAYBOOK) {
            this.setStarted(this.state.started || data.created);
            changed = true;
        }

        if (data.event === EVENT_START_PLAY) {
            this.state.counts.plays++;
            changed = true;
        }

        if (data.event === EVENT_START_TASK) {
            this.state.counts.tasks++;
            changed = true;
        }

        if (data.event === EVENT_STATS_PLAY) {
            this.setStatsEvent(data);
            changed = true;
        }

        if (data.failed) {
            this.state.anyFailed = true;
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
        } else if (this.state.counter > -1) {
            this.setJobStatus(this.state.anyFailed ? 'failed' : 'unknown');
        } else {
            this.setJobStatus('unknown');
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
        const isIncomplete = JOB_STATUS_INCOMPLETE.includes(status);
        const isFinished = JOB_STATUS_FINISHED.includes(status);
        const isAlreadyFinished = JOB_STATUS_FINISHED.includes(this.state.status);

        if (isAlreadyFinished && !isFinished) {
            return;
        }

        if ((isExpectingStats && isIncomplete) || (!isExpectingStats && isFinished)) {
            if (this.latestTime) {
                if (!this.state.finished) {
                    this.setFinished(this.latestTime);
                }

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
        if (!elapsed) return;

        this.state.elapsed = elapsed;
    };

    this.setStarted = started => {
        if (!started) return;

        this.state.started = started;
        this.updateRunningState();
    };

    this.setProjectStatus = status => {
        this.state.scm.status = status;
    };

    this.setProjectUpdateId = id => {
        this.state.scm.id = id;
    };

    this.setInventoryScmStatus = status => {
        this.state.inventoryScm.status = status;
    };

    this.setInventoryScmId = id => {
        this.state.inventoryScm.id = id;
    };

    this.setFinished = time => {
        if (!time) return;

        this.state.finished = time;
        this.updateRunningState();
    };

    this.setEnvironment = env => {
        if (!env) return;

        this.state.environment = env;
    };

    this.setArtifacts = val => {
        if (!val) return;

        this.state.artifacts = val;
    };

    this.setExecutionNode = node => {
        if (!node) return;

        this.state.executionNode = node;
    };

    this.setStatsEvent = data => {
        if (!data) return;

        this.statsEvent = data;
    };

    this.setResultTraceback = traceback => {
        if (!traceback) return;

        this.state.resultTraceback = traceback;
    };

    this.setEventProcessingFinished = val => {
        this.state.event_processing_finished = val;
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

    this.sync = () => {
        const { model } = this;

        return model.http.get({ resource: model.get('id') })
            .then(() => {
                this.setFinished(model.get('finished'));
                this.setElapsed(model.get('elapsed'));
                this.setStarted(model.get('started'));
                this.setJobStatus(model.get('status'));
                this.setEnvironment(model.get('custom_virtualenv'));
                this.setArtifacts(model.get('artifacts'));
                this.setExecutionNode(model.get('execution_node'));
                this.setResultTraceback(model.get('result_traceback'));
                this.setEventProcessingFinished(model.get('event_processing_finished'));

                this.initHostStatusCounts({ model });
                this.initPlaybookCounts({ model });

                this.dispatch();
            });
    };
}

JobStatusService.$inject = [
    'moment',
    'OutputMessageService',
];

export default JobStatusService;
