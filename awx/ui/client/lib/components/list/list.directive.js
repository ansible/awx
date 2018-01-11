const templateUrl = require('~components/list/list.partial.html');

// TODO: figure out emptyListReason scope property

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
        },
        controller: AtListController,
        controllerAs: 'vm',
    };
}

export default atList;
