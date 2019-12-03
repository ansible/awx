import jobTemplateAdd from './add-job-template/main';
import jobTemplateEdit from './edit-job-template/main';
import multiCredential from './multi-credential/main';
import webhookCredential from './webhook-credential';
import hashSetup from './factories/hash-setup.factory';
import CallbackHelpInit from './factories/callback-help-init.factory';
import JobTemplateForm from './job-template.form';

export default
    angular.module('jobTemplates', [jobTemplateAdd.name, jobTemplateEdit.name, multiCredential.name, webhookCredential.name])
        .factory('hashSetup', hashSetup)
        .factory('CallbackHelpInit', CallbackHelpInit)
        .factory('JobTemplateForm', JobTemplateForm);
