function ModelsStrings (BaseString) {
    BaseString.call(this, 'models');

    const { t } = this;
    const ns = this.models;

    ns.labels = {
        CREDENTIAL: t.s('Credentials'),
        CREDENTIAL_TYPE: t.s('Credential Types'),
        INVENTORY: t.s('Inventories'),
        INVENTORY_SCRIPT: t.s('Inventory Scripts'),
        INVENTORY_SOURCE: t.s('Inventory Sources'),
        JOB_TEMPLATE: t.s('Job Templates'),
        ORGANIZATION: t.s('Organizations'),
        PROJECT: t.s('Projects'),
        WORKFLOW_JOB_TEMPLATE_NODE: t.s('Workflow Job Template Nodes')
    };
}

ModelsStrings.$inject = ['BaseStringService'];

export default ModelsStrings;
