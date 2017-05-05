function link (scope, el, attr) {
    scope.show = false;

    el.on('click', createPopover.bind(null, scope));
}

function createPopover (scope, event) {
    scope.show = !scope.show;

    let w = window.outerWidth;
    let h = window.outerHeight;
    let x = event.clientX;
    let y = event.clientY;

    console.log(event);
}

function atPopover (pathService) {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl: pathService.getPartialPath('components/popover/popover'),
        link,
        scope: {
            config: '='
        }
    };
}

atPopover.$inject = ['PathService'];

export default atPopover;
