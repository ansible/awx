import dashboardCounts from './counts/main';
import dashboardGraphs from './graphs/main';
import dashboardLists from './lists/main';
import dashboardDirective from './dashboard.directive';

export default
    angular.module('dashboard', [dashboardCounts.name, dashboardGraphs.name, dashboardLists.name])
        .directive('dashboard', dashboardDirective);
