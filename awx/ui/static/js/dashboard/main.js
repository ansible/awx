import dashboardCounts from 'tower/dashboard/counts/main';
import dashboardGraphs from 'tower/dashboard/graphs/main';
import dashboardLists from 'tower/dashboard/lists/main';
import dashboardDirective from 'tower/dashboard/dashboard.directive';

export default
    angular.module('dashboard', [dashboardCounts.name, dashboardGraphs.name, dashboardLists.name])
        .directive('dashboard', dashboardDirective);
