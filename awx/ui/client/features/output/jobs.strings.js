function JobsStrings (BaseString) {
    BaseString.call(this, 'jobs');

    const { t } = this;
    const ns = this.jobs;

    ns.state = {
        TITLE: t.s('JOBZ')
    };

    ns.warnings = {
        CANCEL_BODY: t.s('Are you sure you want to cancel this job?'),
        CANCEL_HEADER: t.s('Cancel Job'),
    };

    ns.status = {
        RUNNING: t.s('The host status bar will update when the job is complete.'),
        UNAVAILABLE: t.s('Host status information for this job unavailable.'),
    };
}

JobsStrings.$inject = ['BaseStringService'];

export default JobsStrings;
