import { TRUNCATED, TRUNCATE_LENGTH } from './constants';

const templateUrl = require('~components/toggle/toggle-tag.partial.html');

function controller ($scope, TagService, strings) {
    const { tags } = $scope;
    const vm = this;
    vm.truncatedLength = TRUNCATE_LENGTH;
    vm.truncated = TRUNCATED;
    vm.strings = strings;

    vm.toggle = () => {
        vm.truncated = !vm.truncated;
    };

    vm.tags = [];
    // build credentials from tags object
    Object.keys(tags).forEach(key => {
        vm.tags.push(TagService.buildCredentialTag(tags[key]));
    });
}

controller.$inject = ['$scope', 'TagService', 'ComponentsStrings'];

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
