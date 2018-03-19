const templateUrl = require('~features/output/status.partial.html');

const HOST_STATUS_KEYS = ['dark', 'failures', 'changed', 'ok', 'skipped'];

function getHostStatusCounts (statsEvent) {
    const countedHostNames = [];

    const counts = Object.assign(...HOST_STATUS_KEYS.map(key => ({ [key]: 0 })));

    HOST_STATUS_KEYS.forEach(key => {
        const hostData = _.get(statsEvent, ['event_data', key], {});

        Object.keys(hostData).forEach(hostName => {
            const isAlreadyCounted = (countedHostNames.indexOf(hostName) > -1);
            const shouldBeCounted = ((!isAlreadyCounted) && hostData[hostName] > 0);

            if (shouldBeCounted) {
                countedHostNames.push(hostName);
                counts[key]++;
            }
        });
    });

    return counts;
}

function createStatusBarTooltip (key, count) {
    const label = `<span class='HostStatusBar-tooltipLabel'>${key}</span>`;
    const badge = `<span class='badge HostStatusBar-tooltipBadge HostStatusBar-tooltipBadge--${key}'>${count}</span>`;

    return `${label}${badge}`;
}

function atStatusLink (scope, el, attrs, controllers) {
    const [atStatusController] = controllers;

    atStatusController.init(scope);
}

function AtStatusController (strings) {
    const vm = this || {};

    vm.tooltips = {
        running: strings.get('status.RUNNING'),
        unavailable: strings.get('status.UNAVAILABLE'),
    };

    vm.init = scope => {
        const { running, stats } = scope;

        vm.running = running || false;
        vm.setStats(stats);

        scope.$watch('running', value => { vm.running = value; });
        scope.$watch('stats', vm.setStats);
    };

    vm.setStats = stats => {
        const counts = getHostStatusCounts(stats);

        HOST_STATUS_KEYS.forEach(key => {
            const count = counts[key];
            const statusBarElement = $(`.HostStatusBar-${key}`);

            statusBarElement.css('flex', `${count} 0 auto`);

            vm.tooltips[key] = createStatusBarTooltip(key, count);
        });

        vm.statsAreAvailable = Boolean(stats);
    };
}

function atStatus () {
    return {
        templateUrl,
        restrict: 'E',
        require: ['atStatus'],
        controllerAs: 'vm',
        link: atStatusLink,
        controller: [
            'JobStrings',
            AtStatusController
        ],
        scope: {
            running: '=',
            stats: '=',
        },
    };
}

export default atStatus;
