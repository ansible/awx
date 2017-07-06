function atTruncateLink (scope, el, attr, ctrl) {
    let truncateController = ctrl;
    let string = attr.string;
    let maxlength = attr.maxlength;

    truncateController.init(scope, string, maxlength);
}

function AtTruncateController ($filter) {
    let vm = this;
    vm.toolTipContent = 'Copy full revision to clipboard.';

    let maxlength;

    vm.init = (scope, _string_, _maxlength_) => {
        vm.string = _string_;
        maxlength = _maxlength_;
        vm.truncatedString = $filter('limitTo')(vm.string, maxlength, 0);
    }

    vm.copy = function() {
        vm.toolTipContent = 'Copied to clipboard.';

        let textArea = document.createElement("textarea");

        // Place in top-left corner of screen regardless of scroll position.
        textArea.style.position = 'fixed';
        textArea.style.top = 0;
        textArea.style.left = 0;

        // Ensure it has a small width and height. Setting to 1px / 1em
        // doesn't work as this gives a negative w/h on some browsers.
        textArea.style.width = '2em';
        textArea.style.height = '2em';

        // We don't need padding, reducing the size if it does flash render.
        textArea.style.padding = 0;

        // Clean up any borders.
        textArea.style.border = 'none';
        textArea.style.outline = 'none';
        textArea.style.boxShadow = 'none';

        // Avoid flash of white box if rendered for any reason.
        textArea.style.background = 'transparent';

        textArea.value = vm.string;
        document.body.appendChild(textArea);
        textArea.select();

        document.execCommand('copy');

        document.body.removeChild(textArea);
    };

}


function atTruncate($filter, pathService) {
    return {
        restrict: 'EA',
        replace: true,
        transclude: true,
        templateUrl: pathService.getPartialPath('components/truncate/truncate'),
        controller: AtTruncateController,
        controllerAs: 'vm',
        link: atTruncateLink,
        scope: {
            maxLength: '@',
            string: '@'
        }
    }
}

atTruncate.$inject = [
    '$filter',
    'PathService'
];

export default atTruncate;