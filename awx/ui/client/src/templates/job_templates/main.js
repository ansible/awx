import jobTemplateAdd from './add-job-template/main';
import jobTemplateEdit from './edit-job-template/main';
import multiCredential from './multi-credential/main';
import md5Setup from './factories/md-5-setup.factory';
import CallbackHelpInit from './factories/callback-help-init.factory';
import JobTemplateForm from './job-template.form';

export default
    angular.module('jobTemplates', [jobTemplateAdd.name, jobTemplateEdit.name,
        multiCredential.name])
            .factory('md5Setup', md5Setup)
            .factory('CallbackHelpInit', CallbackHelpInit)
            .factory('JobTemplateForm', JobTemplateForm);
