import HostStatusGraphDirective from './host-status-graph.directive';
import DashboardGraphHelpers from '../graph-helpers/main';

export default angular.module('HostStatusGraph', [DashboardGraphHelpers.name])
    .directive('hostStatusGraph', HostStatusGraphDirective);
