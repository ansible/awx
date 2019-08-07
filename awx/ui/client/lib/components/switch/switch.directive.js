const templateUrl = require('~components/switch/switch.partial.html');

function atSwitch () {
    return {
        restrict: 'E',
        replace: true,
        templateUrl,
        scope: {
            hide: '=',
            onToggle: '&',
            switchOn: '=',
            switchDisabled: '=',
            tooltip: '=',
            tooltipString: '@',
            tooltipPlacement: '@',
            tooltipContainer: '@',
            tooltipWatch: '='
        },
    };
}

export default atSwitch;
