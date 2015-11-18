import dashboardCountsDirective from './dashboard-counts.directive';

export default
    angular.module('DashboardCountModules', [])
        .directive('dashboardCounts', dashboardCountsDirective);
