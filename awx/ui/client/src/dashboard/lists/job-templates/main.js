import JobTemplatesListDirective from './job-templates-list.directive';
import systemStatus from '../../../smart-status/main';
import jobSubmissionHelper from '../../../helpers/JobSubmission';

export default angular.module('JobTemplatesList', [systemStatus.name, jobSubmissionHelper.name])
    .directive('jobTemplatesList', JobTemplatesListDirective);
