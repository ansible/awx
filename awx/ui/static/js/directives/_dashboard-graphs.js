import JobStatusGraph from 'tower/directives/job-status-graph';
import HostCountGraph from 'tower/directives/host-count-graph';
import HostStatusGraph from 'tower/directives/host-status-graph';
import AutoSizeModule from 'tower/directives/auto-size-module';
import AdjustGraphSize from 'tower/services/adjust-graph-size';

export default angular.module('DashboardGraphs', [])
    .directive('jobStatusGraph', JobStatusGraph)
    .directive('hostCountGraph', HostCountGraph)
    .directive('hostStatusGraph', HostStatusGraph)
    .directive('autoSizeModule', AutoSizeModule)
    .service('adjustGraphSize', AdjustGraphSize);
