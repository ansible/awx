import { TRUNCATED, TRUNCATE_LENGTH } from './constants';

const templateUrl = require('~components/toggle/toggle-tag.partial.html');

function controller ($scope, TagService) {
    const { tags } = $scope;
    const vm = this;
    vm.truncatedLength = TRUNCATE_LENGTH;
    vm.truncated = TRUNCATED;

    vm.toggle = () => {
        vm.truncated = !vm.truncated;
    };

    vm.tags = [];
    // build credentials from tags object
    Object.keys(tags).forEach(key => {
        vm.tags.push(TagService.buildCredentialTag(tags[key]));
    });
}

controller.$inject = ['$scope', 'TagService'];

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
