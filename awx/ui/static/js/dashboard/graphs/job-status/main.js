import JobStatusGraphDirective from 'tower/dashboard/graphs/job-status/job-status-graph.directive';
import JobStatusGraphService from 'tower/dashboard/graphs/job-status/job-status-graph.service';
import DashboardGraphHelpers from 'tower/dashboard/graphs/graph-helpers/main';
import ApiLoader from 'tower/shared/api-loader';

export default angular.module('JobStatusGraph', [DashboardGraphHelpers.name, ApiLoader.name])
    .directive('jobStatusGraph', JobStatusGraphDirective)
    .service('jobStatusGraphData', JobStatusGraphService);
