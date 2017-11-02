function JobsStrings (BaseString) {
    BaseString.call(this, 'jobs');

    const { t } = this;
    const ns = this.jobs;

    ns.state = {
        TITLE: t.s('JOBZ')
    };
}

JobsStrings.$inject = ['BaseStringService'];

export default JobsStrings;
