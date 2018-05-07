const templateUrl = require('~features/output/stats.partial.html');

let vm;

function createStatsBarTooltip (key, count) {
    const label = `<span class='HostStatusBar-tooltipLabel'>${key}</span>`;
    const badge = `<span class='badge HostStatusBar-tooltipBadge HostStatusBar-tooltipBadge--${key}'>${count}</span>`;

    return `${label}${badge}`;
}

function JobStatsController (strings, { subscribe }) {
    vm = this || {};

    let unsubscribe;

    vm.tooltips = {
        running: strings.get('status.RUNNING'),
        unavailable: strings.get('status.UNAVAILABLE'),
    };

    vm.$onInit = () => {
        vm.download = vm.resource.model.get('related.stdout');
        vm.toggleStdoutFullscreenTooltip = strings.get('expandCollapse.EXPAND');

        unsubscribe = subscribe(({ running, elapsed, counts, stats, hosts }) => {
            vm.plays = counts.plays;
            vm.tasks = counts.tasks;
            vm.hosts = counts.hosts;
            vm.elapsed = elapsed;
            vm.running = running;
            vm.setHostStatusCounts(stats, hosts);
        });
    };

    vm.$onDestroy = () => {
        unsubscribe();
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

    vm.toggleExpanded = () => {
        vm.expanded = !vm.expanded;
        vm.toggleStdoutFullscreenTooltip = vm.expanded ?
            strings.get('expandCollapse.COLLAPSE') :
            strings.get('expandCollapse.EXPAND');
    };
}

JobStatsController.$inject = [
    'JobStrings',
    'JobStatusService',
];

export default {
    templateUrl,
    controller: JobStatsController,
    controllerAs: 'vm',
    bindings: {
        resource: '<',
        expanded: '=',
    },
};
