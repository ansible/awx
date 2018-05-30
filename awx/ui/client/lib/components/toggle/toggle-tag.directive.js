import { TRUNCATED, TRUNCATE_LENGTH } from './constants';

const templateUrl = require('~components/toggle/toggle-tag.partial.html');

function controller () {
    const vm = this;
    vm.truncatedLength = TRUNCATE_LENGTH;
    vm.truncated = TRUNCATED;

    vm.toggle = () => {
        vm.truncated = !vm.truncated;
    };
}

function atToggleTag () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        controller,
        controllerAs: 'vm',
        templateUrl,
        scope: {
            tags: '=',
        },
    };
}

export default atToggleTag;
