const templateUrl = require('~features/output/stats.partial.html');

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

function AtJobStatsController (_strings_, { subscribe }) {
    strings = _strings_;

    const vm = this || {};

    vm.tooltips = {
        running: strings.get('status.RUNNING'),
        unavailable: strings.get('status.UNAVAILABLE'),
    };

    vm.init = scope => {
        const { resource } = scope;

        vm.fullscreen = scope.fullscreen;

        vm.download = resource.model.get('related.stdout');

        vm.toggleStdoutFullscreenTooltip = strings.get('expandCollapse.EXPAND');

        subscribe(({ running, elapsed, counts, stats, hosts }) => {
            vm.plays = counts.plays;
            vm.tasks = counts.tasks;
            vm.hosts = counts.hosts;
            vm.elapsed = elapsed;
            vm.running = running;
            vm.setHostStatusCounts(stats, hosts);
        });
    };

    vm.setHostStatusCounts = (stats, counts) => {
        Object.keys(counts).forEach(key => {
            const count = counts[key];
            const statusBarElement = $(`.HostStatusBar-${key}`);

            statusBarElement.css('flex', `${count} 0 auto`);

            vm.tooltips[key] = createStatsBarTooltip(key, count);
        });

        vm.statsAreAvailable = stats;
    };

    vm.toggleFullscreen = () => {
        vm.fullscreen.isFullscreen = !vm.fullscreen.isFullscreen;
        vm.toggleStdoutFullscreenTooltip = vm.fullscreen.isFullscreen ?
            strings.get('expandCollapse.COLLAPSE') :
            strings.get('expandCollapse.EXPAND');
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
        scope: {
            resource: '=',
            fullscreen: '='
        }
    };
}

export default atJobStats;
