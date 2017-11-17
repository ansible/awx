function TemplatesStrings (BaseString) {
    BaseString.call(this, 'templates');

    let t = this.t;
    let ns = this.templates;

    ns.jobTemplates = {
        deleteJobTemplate: {
            CONFIRM: t.s('The job template is currently being used by other resources. Are you sure you want to delete this job template?')
        }
    };

    ns.workflowJobTemplates = {
        deleteWorkflowJobTemplate: {
            CONFIRM: t.s('Are you sure you want to delete this workflow job template?')
        }
    };
}

TemplatesStrings.$inject = ['BaseStringService'];

export default TemplatesStrings;
