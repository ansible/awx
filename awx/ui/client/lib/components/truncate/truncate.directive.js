const templateUrl = require('~components/truncate/truncate.partial.html');

function atTruncateLink (scope, el, attr, ctrl) {
    const truncateController = ctrl;
    const { string } = attr;
    const { maxlength } = attr;

    truncateController.init(el, string, maxlength);
}

function AtTruncateController (strings) {
    const vm = this;
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

    vm.copyToClipboard = () => {
        vm.tooltip.popover.text = vm.strings.get('truncate.COPIED');

        const textarea = el[0].getElementsByClassName('at-Truncate-textarea')[0];
        textarea.value = string;
        textarea.select();

        document.execCommand('copy');
    };

    vm.tooltip = {
        popover: {
            text: vm.strings.get('truncate.DEFAULT'),
            on: 'mouseover',
            position: 'top',
            icon: 'fa fa-clone',
            resetOnExit: true,
            click: vm.copyToClipboard
        }
    };
}

AtTruncateController.$inject = ['ComponentsStrings'];

function atTruncate () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl,
        controller: AtTruncateController,
        controllerAs: 'vm',
        link: atTruncateLink,
        scope: {
            state: '=',
            maxLength: '@',
            string: '@'
        }
    };
}

export default atTruncate;
