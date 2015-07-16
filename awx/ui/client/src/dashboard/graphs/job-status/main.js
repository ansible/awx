import JobStatusGraphDirective from './job-status-graph.directive';
import JobStatusGraphService from './job-status-graph.service';
import DashboardGraphHelpers from '../graph-helpers/main';
import templateUrl from '../../../shared/template-url/main';

export default angular.module('JobStatusGraph', [DashboardGraphHelpers.name, templateUrl.name])
    .directive('jobStatusGraph', JobStatusGraphDirective)
    .service('jobStatusGraphData', JobStatusGraphService);
