import HostStatusGraphDirective from 'tower/dashboard/graphs/host-status/host-status-graph.directive';
import DashboardGraphHelpers from 'tower/dashboard/graphs/graph-helpers/main';

export default angular.module('HostStatusGraph', [DashboardGraphHelpers.name])
    .directive('hostStatusGraph', HostStatusGraphDirective);
