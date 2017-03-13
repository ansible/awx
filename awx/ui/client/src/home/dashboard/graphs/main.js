import jobStatus from './job-status/main';
import dashboardGraphsDirective from './dashboard-graphs.directive';

export default
    angular.module('DashboardGraphModules', [jobStatus.name])
        .directive('dashboardGraphs', dashboardGraphsDirective);
