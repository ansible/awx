import JobStatusGraphDirective from 'tower/dashboard/graphs/job-status/job-status-graph.directive';
import JobStatusGraphService from 'tower/dashboard/graphs/job-status/job-status-graph.service';
import DashboardGraphHelpers from 'tower/dashboard/graphs/graph-helpers/main';
import templateUrl from 'tower/shared/template-url/main';

export default angular.module('JobStatusGraph', [DashboardGraphHelpers.name, templateUrl.name])
    .directive('jobStatusGraph', JobStatusGraphDirective)
    .service('jobStatusGraphData', JobStatusGraphService);
