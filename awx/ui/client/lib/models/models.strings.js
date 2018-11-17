function ModelsStrings (BaseString) {
    BaseString.call(this, 'models');

    const { t } = this;
    const ns = this.models;

    ns.credentials = {
        LABEL: t.s('Credentials')
    };

    ns.credential_types = {
        LABEL: t.s('Credential Types')
    };

    ns.inventories = {
        LABEL: t.s('Inventories')
    };

    ns.inventory_scripts = {
        LABEL: t.s('Inventory Scripts')

    };

    ns.inventory_sources = {
        LABEL: t.s('Inventory Sources')

    };

    ns.job_templates = {
        LABEL: t.s('Job Templates')

    };

    ns.organizations = {
        LABEL: t.s('Organizations')

    };

    ns.projects = {
        LABEL: t.s('Projects')

    };

    ns.workflow_job_templates = {
        LABEL: t.s('Workflow Job Templates')
    };

    ns.workflow_job_template_nodes = {
        LABEL: t.s('Workflow Job Template Nodes')

    };
}

ModelsStrings.$inject = ['BaseStringService'];

export default ModelsStrings;
