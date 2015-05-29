import dashboardCountsDirective from 'tower/dashboard/counts/dashboard-counts.directive';

export default
    angular.module('DashboardCountModules', [])
        .directive('dashboardCounts', dashboardCountsDirective);
