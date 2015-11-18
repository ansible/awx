import hostStatus from './host-status/main';
import jobStatus from './job-status/main';
import dashboardGraphsDirective from './dashboard-graphs.directive';

export default
    angular.module('DashboardGraphModules', [hostStatus.name, jobStatus.name])
        .directive('dashboardGraphs', dashboardGraphsDirective);
