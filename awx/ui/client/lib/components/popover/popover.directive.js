const DEFAULT_POSITION = 'right';
const DEFAULT_ACTION = 'click';
const DEFAULT_ICON = 'fa fa-question-circle';
const DEFAULT_ALIGNMENT = 'inline';
const DEFAULT_ARROW_HEIGHT = 16;
const DEFAULT_PADDING = 10;
const DEFAULT_REFRESH_DELAY = 50;

function atPopoverLink (scope, el, attr, controllers) {
    let popoverController = controllers[0];
    let container = el[0];
    let popover = container.getElementsByClassName('at-Popover-container')[0];
    let icon = container.getElementsByTagName('i')[0];

    let done = scope.$watch('state', () => {
        popoverController.init(scope, container, icon, popover);
        done();
    });
}

function AtPopoverController () {
    let vm = this;

    let container;
    let icon;
    let popover;
    let scope;

    vm.init = (_scope_, _container_, _icon_, _popover_) => {
        scope = _scope_;
        icon = _icon_;
        popover = _popover_;

        scope.popover = scope.state.popover || {};

        scope.popover.text = scope.state.help_text || scope.popover.text;
        scope.popover.title = scope.state.label || scope.popover.title;
        scope.popover.inline = scope.popover.inline || DEFAULT_ALIGNMENT;
        scope.popover.position = scope.popover.position || DEFAULT_POSITION;
        scope.popover.icon = scope.popover.icon || DEFAULT_ICON;
        scope.popover.on = scope.popover.on || DEFAULT_ACTION;

        icon.addEventListener(scope.popover.on, vm.createDisplayListener());

        scope.$watch('popover.text', vm.refresh);

        if (scope.popover.click) {
            icon.addEventListener('click', scope.popover.click);
        }
    };

    vm.createDismissListener = (createEvent) => {
        return event => {
            event.stopPropagation();

            if (vm.isClickWithinPopover(event, popover)) {
                return;
            }

            vm.dismiss();

            window.removeEventListener(scope.popover.on, vm.dismissListener);
            window.removeEventListener('resize', vm.dismissListener);
        };
    };

    vm.dismiss = () => {
        vm.open = false;

        popover.style.visibility = 'hidden';
        popover.style.opacity = 0;
    };

    vm.isClickWithinPopover = (event, popover) => {
        let box = popover.getBoundingClientRect();

        let x = event.clientX;
        let y = event.clientY;

        if ((x <= box.right && x >= box.left) && (y >= box.top && y <= box.bottom)) {
            return true;
        }

        return false;
    };

    vm.createDisplayListener = () => {
        return event => {
            if (vm.open) {
                return;
            }

            event.stopPropagation();

            vm.display();

            vm.dismissListener = vm.createDismissListener(event);

            window.addEventListener(scope.popover.on, vm.dismissListener);
            window.addEventListener('resize', vm.dismissListener);
        };
    };

    vm.refresh = () => {
        if (!vm.open) {
            return;
        }

        vm.dismiss();
        window.setTimeout(vm.display, DEFAULT_REFRESH_DELAY);
    };

    vm.getPositions = () => {
        let arrow = popover.getElementsByClassName('at-Popover-arrow')[0];

        arrow.style.lineHeight = `${DEFAULT_ARROW_HEIGHT}px`;
        arrow.children[0].style.lineHeight = `${DEFAULT_ARROW_HEIGHT}px`;

        let data = {
            arrow,
            icon: icon.getBoundingClientRect(),
            popover: popover.getBoundingClientRect(),
            windowHeight: window.innerHeight
        };

        data.cx = Math.floor(data.icon.left + (data.icon.width / 2));
        data.cy = Math.floor(data.icon.top + (data.icon.height / 2));

        return data;
    };

    vm.display = () => {
        vm.open = true;

        let positions = vm.getPositions();

        popover.style.visibility = 'visible';
        popover.style.opacity = 1;

        if (scope.popover.position === 'right') {
            vm.displayRight(positions);
        } else if (scope.popover.position === 'top') {
            vm.displayTop(positions);
        }
    };

    vm.displayRight = (pos) => {
        let arrowTop = Math.floor((pos.cy - (pos.icon.height / 2)));
        let arrowLeft = pos.cx + DEFAULT_PADDING;

        let popoverTop;
        let popoverLeft = arrowLeft + DEFAULT_PADDING - 1;

        if (pos.cy < (pos.popover.height / 2)) {
            popoverTop = DEFAULT_PADDING;
        } else {
            popoverTop = Math.floor((pos.cy - pos.popover.height / 2));
        }

        pos.arrow.style.top = `${arrowTop}px`;
        pos.arrow.style.left = `${arrowLeft}px`;

        popover.style.top = `${popoverTop}px`;
        popover.style.left = `${popoverLeft}px`;
    };

    vm.displayTop = (pos) => {
        let arrowTop = pos.icon.top - pos.icon.height;
        let arrowLeft = Math.floor(pos.icon.right - pos.icon.width - (pos.arrow.style.width / 2));

        let popoverTop = pos.icon.top - pos.popover.height - DEFAULT_PADDING;
        let popoverLeft = Math.floor(pos.cx - (pos.popover.width / 2));

        pos.arrow.style.top = `${arrowTop}px`; 
        pos.arrow.style.left = `${arrowLeft}px`; 

        popover.style.top = `${popoverTop}px`;
        popover.style.left = `${popoverLeft}px`;
    };
}

function atPopover (pathService) {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        require: ['atPopover'],
        templateUrl: pathService.getPartialPath('components/popover/popover'),
        controller: AtPopoverController,
        controllerAs: 'vm',
        link: atPopoverLink,
        scope: {
            state: '='
        }
    };
}

atPopover.$inject = [
    'PathService'
];

export default atPopover;
