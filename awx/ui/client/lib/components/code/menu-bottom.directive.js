const templateUrl = require('~components/code/menu-bottom.partial.html');

function atCodeMenuBottomLink (scope, element, attrs, controller) {
    controller.init(scope, element);
}

function AtCodeMenuBottomController () {
    const vm = this || {};

    let element;

    vm.init = (_scope_, _element_) => {
        element = _element_;
    };

    vm.scroll = () => {
        const container = element.find('.at-Stdout-container')[0];

        container.scrollTop = container.scrollHeight;
    };
}

AtCodeMenuBottomController.$inject = [];

function atCodeMenuBottom () {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: 'atCodeMenuBottom',
        templateUrl,
        controller: AtCodeMenuBottomController,
        controllerAs: 'vm',
        link: atCodeMenuBottomLink,
        scope: {
            state: '=',
        }
    };
}

export default atCodeMenuBottom;
