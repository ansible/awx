function atPopoverLink (scope, el, attr, controllers) {
    let popoverController = controllers[0];
    let icon = el[0];
    let popover = icon.getElementsByClassName('at-Popover-container')[0];

    popoverController.init(icon, popover);
}

function AtPopoverController () {
    let vm = this;

    let icon;
    let popover;

    vm.init = (_icon_, _popover_) => {
        icon = _icon_;
        popover = _popover_;

        icon.addEventListener('click', vm.createDisplayListener());
    };

    vm.createDismissListener = (createEvent) => {
        return event => {
            event.stopPropagation();

            vm.open = false;

            popover.style.visibility = 'hidden';
            popover.style.opacity = 0;

            window.removeEventListener('click', vm.dismissListener);
            window.removeEventListener('resize', vm.dismissListener);
        };
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

            if (cy < (pHeight / 2)) {
                popover.style.top = '10px';
            } else {
                popover.style.top = (cy - pHeight / 2) + 'px';
            }

            popover.style.left = cx + 'px';

            arrow.style.top = iPos.top + 'px'; 
            arrow.style.left = iPos.left + 20 + 'px'; 

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
