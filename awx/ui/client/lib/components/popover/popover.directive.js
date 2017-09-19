const templateUrl = require('~components/popover/popover.partial.html');

const DEFAULT_POSITION = 'right';
const DEFAULT_ACTION = 'click';
const DEFAULT_ICON = 'fa fa-question-circle';
const DEFAULT_ALIGNMENT = 'inline';
const DEFAULT_ARROW_HEIGHT = 14;
const DEFAULT_PADDING = 10;
const DEFAULT_REFRESH_DELAY = 50;
const DEFAULT_RESET_ON_EXIT = false;

function atPopoverLink (scope, el, attr, controllers) {
    const popoverController = controllers[0];
    const container = el[0];
    const popover = container.getElementsByClassName('at-Popover-container')[0];
    const icon = container.getElementsByTagName('i')[0];

    const done = scope.$watch('state', () => {
        popoverController.init(scope, container, icon, popover);
        done();
    });
}

function AtPopoverController () {
    const vm = this;

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
        scope.popover.resetOnExit = scope.popover.resetOnExit || DEFAULT_RESET_ON_EXIT;
        scope.popover.arrowHeight = scope.popover.arrowHeight || DEFAULT_ARROW_HEIGHT;

        if (scope.popover.resetOnExit) {
            scope.originalText = scope.popover.text;
            scope.originalTitle = scope.popover.title;
        }

        icon.addEventListener(scope.popover.on, vm.createDisplayListener());

        scope.$watch('popover.text', vm.refresh);

        if (scope.popover.click) {
            icon.addEventListener('click', scope.popover.click);
        }
    };

    vm.createDismissListener = () => event => {
        event.stopPropagation();

        if (vm.isClickWithinPopover(event, popover)) {
            return;
        }

        vm.dismiss();

        if (scope.popover.on === 'mouseenter') {
            icon.removeEventListener('mouseleave', vm.dismissListener);
        } else {
            window.addEventListener(scope.popover.on, vm.dismissListener);
        }

        window.removeEventListener('resize', vm.dismissListener);
    };

    vm.dismiss = (refresh) => {
        if (!refresh && scope.popover.resetOnExit) {
            scope.popover.text = scope.originalText;
            scope.popover.title = scope.originalTitle;
        }

        vm.open = false;

        popover.style.visibility = 'hidden';
        popover.style.opacity = 0;
    };

    vm.isClickWithinPopover = (event, popoverEl) => {
        const box = popoverEl.getBoundingClientRect();

        const x = event.clientX;
        const y = event.clientY;

        if ((x <= box.right && x >= box.left) && (y >= box.top && y <= box.bottom)) {
            return true;
        }

        return false;
    };

    vm.createDisplayListener = () => event => {
        if (vm.open) {
            return;
        }

        event.stopPropagation();

        vm.display();

        vm.dismissListener = vm.createDismissListener(event);

        if (scope.popover.on === 'mouseenter') {
            icon.addEventListener('mouseleave', vm.dismissListener);
        } else {
            window.addEventListener(scope.popover.on, vm.dismissListener);
        }

        window.addEventListener('resize', vm.dismissListener);
    };

    vm.refresh = () => {
        if (!vm.open) {
            return;
        }

        vm.dismiss(true);
        window.setTimeout(vm.display, DEFAULT_REFRESH_DELAY);
    };

    vm.getPositions = () => {
        const arrow = popover.getElementsByClassName('at-Popover-arrow')[0];

        arrow.style.lineHeight = `${DEFAULT_ARROW_HEIGHT}px`;
        arrow.children[0].style.lineHeight = `${scope.popover.arrowHeight}px`;

        const data = {
            arrow,
            icon: icon.getBoundingClientRect(),
            popover: popover.getBoundingClientRect(),
            windowHeight: window.innerHeight
        };

        data.cx = Math.floor(data.icon.left + (data.icon.width / 2));
        data.cy = Math.floor(data.icon.top + (data.icon.height / 2));
        data.rightBoundary = Math.floor(data.icon.right);

        return data;
    };

    vm.display = () => {
        vm.open = true;

        const positions = vm.getPositions();

        popover.style.visibility = 'visible';
        popover.style.opacity = 1;

        if (scope.popover.position === 'right') {
            vm.displayRight(positions);
        } else if (scope.popover.position === 'top') {
            vm.displayTop(positions);
        }
    };

    vm.displayRight = (pos) => {
        const arrowHeight = pos.arrow.offsetHeight;
        const arrowLeft = pos.rightBoundary + DEFAULT_PADDING;
        const popoverLeft = arrowLeft + DEFAULT_PADDING - 1;

        let popoverTop;
        if (pos.cy < (pos.popover.height / 2)) {
            popoverTop = DEFAULT_PADDING;
        } else {
            popoverTop = Math.floor((pos.cy - pos.popover.height / 2));
        }

        const arrowTop = Math.floor(popoverTop + (pos.popover.height / 2) - (arrowHeight / 2));

        pos.arrow.style.top = `${arrowTop}px`;
        pos.arrow.style.left = `${arrowLeft}px`;

        popover.style.top = `${popoverTop}px`;
        popover.style.left = `${popoverLeft}px`;
    };

    vm.displayTop = (pos) => {
        const arrowTop = pos.icon.top - pos.icon.height - DEFAULT_PADDING;
        const arrowLeft = Math.floor(pos.icon.right - pos.icon.width - (pos.arrow.style.width / 2));

        const popoverTop = pos.icon.top - pos.popover.height - pos.icon.height - 5;
        const popoverLeft = Math.floor(pos.cx - (pos.popover.width / 2));

        pos.arrow.style.top = `${arrowTop}px`;
        pos.arrow.style.left = `${arrowLeft}px`;

        popover.style.top = `${popoverTop}px`;
        popover.style.left = `${popoverLeft}px`;
    };
}

function atPopover () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        require: ['atPopover'],
        templateUrl,
        controller: AtPopoverController,
        controllerAs: 'vm',
        link: atPopoverLink,
        scope: {
            state: '='
        }
    };
}

export default atPopover;
