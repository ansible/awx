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

    // Let the controller handle what type of tag should be passed to the directive
    // e.g. default tag, crential tag, etc.
    Object.keys(tags).forEach(key => {
        if ($scope.tagType === 'cred') {
            vm.tags.push(TagService.buildCredentialTag(tags[key]));
        } else {
            vm.tags.push(TagService.buildTag(tags[key]));
        }
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
            tagType: '@',
        },
    };
}

export default atToggleTag;
