import AutoSize from 'tower/dashboard/graphs/graph-helpers/auto-size.directive';
import AdjustGraphSize from 'tower/dashboard/graphs/graph-helpers/adjust-graph-size.service';

export default angular.module('DashboardGraphHelpers', [])
    .directive('autoSizeModule', AutoSize)
    .service('adjustGraphSize', AdjustGraphSize);
