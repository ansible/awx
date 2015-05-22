import JobTemplatesListDirective from 'tower/dashboard/lists/job-templates/job-templates-list.directive';
import systemStatus from 'tower/smart-status/main';
import jobSubmissionHelper from 'tower/helpers/JobSubmission';

export default angular.module('JobTemplatesList', [systemStatus.name, jobSubmissionHelper.name])
    .directive('jobTemplatesList', JobTemplatesListDirective);
