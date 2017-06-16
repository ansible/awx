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

    vm.init = (scope, _container_, _icon_, _popover_) => {
        icon = _icon_;
        popover = _popover_;
        scope.inline = true;

        icon.addEventListener('click', vm.createDisplayListener());
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

            window.removeEventListener('click', vm.dismissListener);
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

            let iPos = icon.getBoundingClientRect();
            let pPos = popover.getBoundingClientRect();

            let wHeight = window.clientHeight;
            let pHeight = pPos.height;

            let cx = Math.floor(iPos.left + (iPos.width / 2));
            let cy = Math.floor(iPos.top + (iPos.height / 2));

            arrow.style.top = (iPos.top - iPos.height) + 'px'; 
            arrow.style.left = iPos.right + 'px'; 

            if (cy < (pHeight / 2)) {
                popover.style.top = '10px';
            } else {
                popover.style.top = (cy - pHeight / 2) + 'px';
            }

            popover.style.left = cx + 'px';
            popover.style.visibility = 'visible';
            popover.style.opacity = 1;

            vm.dismissListener = vm.createDismissListener(event);

            window.addEventListener('click', vm.dismissListener);
            window.addEventListener('resize', vm.dismissListener);
        };
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
