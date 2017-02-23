import AutoSize from './auto-size.directive';
import AdjustGraphSize from './adjust-graph-size.service';

export default angular.module('DashboardGraphHelpers', [])
    .directive('autoSizeModule', AutoSize)
    .service('adjustGraphSize', AdjustGraphSize);
