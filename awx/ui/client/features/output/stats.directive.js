const templateUrl = require('~features/output/stats.partial.html');

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

    counts.hosts = countedHostNames.length;

    return counts;
}

function createStatsBarTooltip (key, count) {
    const label = `<span class='HostStatusBar-tooltipLabel'>${key}</span>`;
    const badge = `<span class='badge HostStatusBar-tooltipBadge HostStatusBar-tooltipBadge--${key}'>${count}</span>`;

    return `${label}${badge}`;
}

function atStatsLink (scope, el, attrs, controllers) {
    const [atStatsController] = controllers;

    atStatsController.init(scope);
}

function AtStatsController (strings) {
    const vm = this || {};

    vm.tooltips = {
        running: strings.get('status.RUNNING'),
        unavailable: strings.get('status.UNAVAILABLE'),
    };

    vm.init = scope => {
        const { download, elapsed, running, stats, plays, tasks } = scope;

        vm.download = download;
        vm.plays = plays;
        vm.tasks = tasks;
        vm.elapsed = elapsed;
        vm.running = running || false;

        vm.setStats(stats);

        scope.$watch('elapsed', value => { vm.elapsed = value; });
        scope.$watch('running', value => { vm.running = value; });
        scope.$watch('plays', value => { vm.plays = value; });
        scope.$watch('tasks', value => { vm.tasks = value; });

        scope.$watch('stats', vm.setStats);
    };

    vm.setStats = stats => {
        const counts = getHostStatusCounts(stats);

        HOST_STATUS_KEYS.forEach(key => {
            const count = counts[key];
            const statusBarElement = $(`.HostStatusBar-${key}`);

            statusBarElement.css('flex', `${count} 0 auto`);

            vm.tooltips[key] = createStatsBarTooltip(key, count);
        });

        vm.hosts = counts.hosts;
        vm.statsAreAvailable = Boolean(stats);
    };
}

function atStats () {
    return {
        templateUrl,
        restrict: 'E',
        require: ['atStats'],
        controllerAs: 'vm',
        link: atStatsLink,
        controller: [
            'JobStrings',
            AtStatsController
        ],
        scope: {
            download: '=',
            elapsed: '=',
            running: '=',
            stats: '=',
            plays: '=',
            tasks: '=',
        },
    };
}

export default atStats;
