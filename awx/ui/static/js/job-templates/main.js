import deleteJobTemplate from './delete-job-template.service';

export default
    angular.module('jobTemplates', [])
        .service('deleteJobTemplate', deleteJobTemplate);
