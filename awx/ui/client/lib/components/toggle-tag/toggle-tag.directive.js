import { IS_TRUNCATED, TRUNCATE_LENGTH } from './constants';

const templateUrl = require('~components/toggle-tag/toggle-tag.partial.html');

function controller (strings) {
    const vm = this;
    vm.truncatedLength = TRUNCATE_LENGTH;
    vm.isTruncated = IS_TRUNCATED;
    vm.strings = strings;

    vm.toggle = () => {
        vm.isTruncated = !vm.isTruncated;
    };
}

controller.$inject = ['ComponentsStrings'];

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
