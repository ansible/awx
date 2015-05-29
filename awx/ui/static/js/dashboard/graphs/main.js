import hostStatus from 'tower/dashboard/graphs/host-status/main';
import jobStatus from 'tower/dashboard/graphs/job-status/main';
import dashboardGraphsDirective from 'tower/dashboard/graphs/dashboard-graphs.directive';

export default
    angular.module('DashboardGraphModules', [hostStatus.name, jobStatus.name])
        .directive('dashboardGraphs', dashboardGraphsDirective);
