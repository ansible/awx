const templateUrl = require('~src/templates/job_templates/webhook-credential/webhook-credential-input.partial.html');
export default {
    templateUrl,
    controllerAs: 'vm',
    bindings: {
        isFieldDisabled: '<',
        tagName: '<',
        onLookupClick: '<',
        onTagDelete: '<',
    },
};
