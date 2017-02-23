import dashboardCounts from './counts/main';
import dashboardGraphs from './graphs/main';
import dashboardLists from './lists/main';
import dashboardDirective from './dashboard.directive';
import dashboardHosts from './hosts/main';

export default
    angular.module('dashboard', [dashboardHosts.name, dashboardCounts.name, dashboardGraphs.name, dashboardLists.name])
        .directive('dashboard', dashboardDirective);
