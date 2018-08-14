import { OUTPUT_NO_COUNT_JOB_TYPES } from './constants';

const templateUrl = require('~features/output/stats.partial.html');

let vm;

function createStatsBarTooltip (key, count) {
    const label = `<span class='HostStatusBar-tooltipLabel'>${key}</span>`;
    const badge = `<span class='badge HostStatusBar-tooltipBadge HostStatusBar-tooltipBadge--${key}'>${count}</span>`;

    return `${label}${badge}`;
}

function JobStatsController (strings, { subscribe }) {
    vm = this || {};
    vm.strings = strings;

    let unsubscribe;

    vm.tooltips = {
        running: strings.get('status.RUNNING'),
        unavailable: strings.get('status.UNAVAILABLE'),
    };

    vm.$onInit = () => {
        vm.hideCounts = OUTPUT_NO_COUNT_JOB_TYPES.includes(vm.resource.model.get('type'));
        vm.download = vm.resource.model.get('related.stdout');
        vm.tooltips.toggleExpand = vm.expanded ?
            strings.get('tooltips.COLLAPSE_OUTPUT') :
            strings.get('tooltips.EXPAND_OUTPUT');

        unsubscribe = subscribe(({ running, elapsed, counts, hosts }) => {
            vm.plays = counts.plays;
            vm.tasks = counts.tasks;
            vm.hosts = counts.hosts;
            vm.elapsed = elapsed;
            vm.running = running;
            vm.setHostStatusCounts(hosts);
        });
    };

    vm.$onDestroy = () => {
        unsubscribe();
    };

    vm.setHostStatusCounts = counts => {
        let statsAreAvailable;

        Object.keys(counts).forEach(key => {
            const count = counts[key];
            const statusBarElement = $(`.HostStatusBar-${key}`);

            statusBarElement.css('flex', `${count} 0 auto`);

            vm.tooltips[key] = createStatsBarTooltip(key, count);

            if (count) statsAreAvailable = true;
        });

        vm.statsAreAvailable = statsAreAvailable;
    };

    vm.toggleExpanded = () => {
        vm.expanded = !vm.expanded;
        vm.tooltips.toggleExpand = vm.expanded ?
            strings.get('tooltips.COLLAPSE_OUTPUT') :
            strings.get('tooltips.EXPAND_OUTPUT');
    };
}

JobStatsController.$inject = [
    'OutputStrings',
    'OutputStatusService',
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
