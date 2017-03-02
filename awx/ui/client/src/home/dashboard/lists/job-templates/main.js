import JobTemplatesListDirective from './job-templates-list.directive';
import systemStatus from '../../../../smart-status/main';

export default angular.module('JobTemplatesList', [systemStatus.name])
    .directive('jobTemplatesList', JobTemplatesListDirective);
