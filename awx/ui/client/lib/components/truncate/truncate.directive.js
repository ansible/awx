function atTruncateLink (scope, el, attr, ctrl) {
    let truncateController = ctrl;
    let string = attr.string;
    let maxlength = attr.maxlength;

    truncateController.init(el, string, maxlength);
}

function AtTruncateController (strings) {
    let vm = this;
    let el;
    let string;
    let maxlength;
    vm.strings = strings;

    vm.init = (_el_, _string_, _maxlength_) => {
        el = _el_;
        string = _string_;
        maxlength = _maxlength_;
        vm.truncatedString = string.substring(0, maxlength);
    };

    vm.tooltip = {
        popover: {
            text: vm.strings.components.truncate.DEFAULT,
            on: 'mouseover',
            position: 'top',
            icon: 'fa fa-clone',
            resetOnExit: true,
            click: copyToClipboard
        }
    };

    function copyToClipboard() {
        vm.tooltip.popover.text = vm.strings.components.truncate.COPIED;

        let textarea = el[0].getElementsByClassName('at-Truncate-textarea')[0];
        textarea.value = string;
        textarea.select();

        document.execCommand('copy');
    };
}

AtTruncateController.$inject = ['ComponentsStrings'];

function atTruncate(pathService) {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl: pathService.getPartialPath('components/truncate/truncate'),
        controller: AtTruncateController,
        controllerAs: 'vm',
        link: atTruncateLink,
        scope: {
            state: '=',
            maxLength: '@',
            string: '@'
        }
    }
}

atTruncate.$inject = [
    'PathService'
];

export default atTruncate;