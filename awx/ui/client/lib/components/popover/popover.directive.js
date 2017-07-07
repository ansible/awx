const DEFAULT_POSITION = 'right';
const DEFAULT_ACTION = 'click';
const DEFAULT_ICON = 'fa fa-question-circle';
const DEFAULT_ALIGNMENT = 'inline';
const DEFAULT_ARROW_HEIGHT = 16;
const DEFAULT_PADDING = 10;

function atPopoverLink (scope, el, attr, controllers) {
    let popoverController = controllers[0];
    let container = el[0];
    let popover = container.getElementsByClassName('at-Popover-container')[0];
    let icon = container.getElementsByTagName('i')[0];

    popoverController.init(scope, container, icon, popover);
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

        scope.state.popover = scope.state.popover || {};

        vm.inline = scope.state.popover.inline || DEFAULT_ALIGNMENT;
        vm.position = scope.state.popover.position || DEFAULT_POSITION;
        vm.icon = scope.state.popover.icon || DEFAULT_ICON;
        vm.text = scope.state.popover.text || scope.state.help_text;
        vm.title = scope.state.popover.title || scope.state.label;
        vm.on = scope.state.popover.on || DEFAULT_ACTION;

        icon.addEventListener(vm.on, vm.createDisplayListener());
    };

    vm.createDismissListener = (createEvent) => {
        return event => {
            event.stopPropagation();

            if (vm.isClickWithinPopover(event, popover)) {
                return;
            }

            vm.open = false;

            popover.style.visibility = 'hidden';
            popover.style.opacity = 0;

            window.removeEventListener(vm.on, vm.dismissListener);
            window.removeEventListener('resize', vm.dismissListener);
        };
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

            vm.open = true;


            let arrow = popover.getElementsByClassName('at-Popover-arrow')[0];
            arrow.style.lineHeight = `${DEFAULT_ARROW_HEIGHT}px`;
            arrow.children[0].style.lineHeight = `${DEFAULT_ARROW_HEIGHT}px`;

            let pos = {
                icon: icon.getBoundingClientRect(),
                popover: popover.getBoundingClientRect(),
                windowHeight: window.innerHeight,
            };

            pos.cx = Math.floor(pos.icon.left + (pos.icon.width / 2));
            pos.cy = Math.floor(pos.icon.top + (pos.icon.height / 2));

            if (vm.position === 'right') {
                vm.displayRight(arrow, pos);
            } else if (vm.position === 'top') {
                vm.displayTop(arrow, pos);
            }

            popover.style.visibility = 'visible';
            popover.style.opacity = 1;

            vm.dismissListener = vm.createDismissListener(event);

            window.addEventListener(vm.on, vm.dismissListener);
            window.addEventListener('resize', vm.dismissListener);
        };
    };

    vm.displayRight = (arrow, pos) => {
        let arrowTop = Math.floor((pos.cy - (pos.icon.height / 2)));
        let arrowLeft = pos.cx + DEFAULT_PADDING;

        let popoverTop;
        let popoverLeft = arrowLeft + DEFAULT_PADDING - 1;

        if (pos.cy < (pos.popover.height / 2)) {
            popoverTop = DEFAULT_PADDING;
        } else {
            popoverTop = Math.floor((pos.cy - pos.popover.height / 2));
        }

        arrow.style.top = `${arrowTop}px`;
        arrow.style.left = `${arrowLeft}px`;

        popover.style.top = `${popoverTop}px`;
        popover.style.left = `${popoverLeft}px`;
    };

    vm.displayTop = (arrow, pos) => {
        let arrowTop = pos.icon.top - pos.icon.height;
        let arrowLeft = Math.floor(pos.icon.right - pos.icon.width - (arrow.style.width / 2));

        let popoverTop = pos.icon.top - pos.popover.height - DEFAULT_PADDING;
        let popoverLeft = Math.floor(pos.cx - (pos.popover.width / 2));

        arrow.style.top = `${arrowTop}px`; 
        arrow.style.left = `${arrowLeft}px`; 

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
