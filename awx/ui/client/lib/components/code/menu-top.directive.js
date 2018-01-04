const templateUrl = require('~components/code/menu-top.partial.html');

function atCodeMenuTopLink (scope, element, attrs, controller) {
    controller.init(scope, element);
}

function AtCodeMenuTopController () {
    const vm = this || {};

    let element;
    let scope;

    vm.init = (_scope_, _element_) => {
        scope = _scope_;
        element = _element_;

        scope.state.isExpanded = scope.state.isExpanded || false;
    };

    vm.scroll = () => {
        const container = element.parent().find('.at-Stdout-container')[0];

        container.scrollTop = 0;
    };

    vm.expand = () => {
        scope.state.isExpanded = !scope.state.isExpanded;
        scope.state.expand();
    };
}

AtCodeMenuTopController.$inject = [];

function atCodeMenuTop () {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: 'atCodeMenuTop',
        templateUrl,
        controller: AtCodeMenuTopController,
        controllerAs: 'vm',
        link: atCodeMenuTopLink,
        scope: {
            state: '=',
        }
    };
}

export default atCodeMenuTop;
