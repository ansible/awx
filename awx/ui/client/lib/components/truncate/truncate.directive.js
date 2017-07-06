function atTruncateLink (scope, el, attr, ctrl) {
    let truncateController = ctrl;
    let string = attr.atTruncate;
    let maxlength = attr.maxlength;

    truncateController.init(scope, string, maxlength);
}

function AtTruncateController ($filter) {
    let vm = this;

    let string,
        maxlength;

    vm.init = (scope, _string_, _maxlength_) => {
        string = _string_;
        maxlength = _maxlength_;
        vm.truncatedString = $filter('limitTo')(string, maxlength, 0);
    }

}


function atTruncate($filter) {
    return {
        restrict: 'EA',
        replace: true,
        transclude: true,
        template: '<span>{{vm.truncatedString}}</span>',
        controller: AtTruncateController,
        controllerAs: 'vm',
        link: atTruncateLink,
        scope: {
            maxLength: '@'
        }
    }
}

atTruncate.$inject = [
    '$filter'
];

export default atTruncate;