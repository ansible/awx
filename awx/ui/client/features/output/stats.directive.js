const templateUrl = require('~features/output/stats.partial.html');

let status;
let strings;

function createStatsBarTooltip (key, count) {
    const label = `<span class='HostStatusBar-tooltipLabel'>${key}</span>`;
    const badge = `<span class='badge HostStatusBar-tooltipBadge HostStatusBar-tooltipBadge--${key}'>${count}</span>`;

    return `${label}${badge}`;
}

function atJobStatsLink (scope, el, attrs, controllers) {
    const [atJobStatsController] = controllers;

    atJobStatsController.init(scope);
}

function AtJobStatsController (_strings_, _status_) {
    status = _status_;
    strings = _strings_;

    const vm = this || {};

    vm.tooltips = {
        running: strings.get('status.RUNNING'),
        unavailable: strings.get('status.UNAVAILABLE'),
    };

    vm.init = scope => {
        const { resource } = scope;

        vm.download = resource.model.get('related.stdout');

        vm.setHostStatusCounts(status.getHostStatusCounts());

        scope.$watch(status.getPlayCount, value => { vm.plays = value; });
        scope.$watch(status.getTaskCount, value => { vm.tasks = value; });
        scope.$watch(status.getElapsed, value => { vm.elapsed = value; });
        scope.$watch(status.getHostCount, value => { vm.hosts = value; });
        scope.$watch(status.isRunning, value => { vm.running = value; });

        scope.$watchCollection(status.getHostStatusCounts, vm.setHostStatusCounts);
    };

    vm.setHostStatusCounts = counts => {
        Object.keys(counts).forEach(key => {
            const count = counts[key];
            const statusBarElement = $(`.HostStatusBar-${key}`);

            statusBarElement.css('flex', `${count} 0 auto`);

            vm.tooltips[key] = createStatsBarTooltip(key, count);
        });

        vm.statsAreAvailable = Boolean(status.getStatsEvent());
    };
}

function atJobStats () {
    return {
        templateUrl,
        restrict: 'E',
        require: ['atJobStats'],
        controllerAs: 'vm',
        link: atJobStatsLink,
        controller: [
            'JobStrings',
            'JobStatusService',
            AtJobStatsController
        ],
        scope: { resource: '=', },
    };
}

export default atJobStats;
