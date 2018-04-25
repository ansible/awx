const templateUrl = require('~components/list/list.partial.html');

function atListLink (scope, element, attrs) {
    if (!attrs.results) {
        throw new Error('at-list directive requires results attr to set up the empty list properly');
    }
}

function AtListController (strings) {
    this.strings = strings;
}

AtListController.$inject = ['ComponentsStrings'];

function atList () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl,
        scope: {
            results: '=',
            emptyListReason: '@'
        },
        link: atListLink,
        controller: AtListController,
        controllerAs: 'vm',
    };
}

export default atList;
