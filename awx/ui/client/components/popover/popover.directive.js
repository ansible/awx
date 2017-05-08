let pathService;

function link (scope, el, attr) {
    let icon = el[0];
    let popover = icon.getElementsByClassName('at-Popover-container')[0];

    el.on('click', createDisplayListener(icon, popover));
}

function createDisplayListener (icon, popover) {
    return event => {
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

        let dismissListener = createDismissListener(popover);

        window.addEventListener('mousedown', dismissListener);
        window.addEventListener('resize', dismissListener);
    };
}

function createDismissListener (popover) {
    return function dismissListener () {
        popover.style.visibility = 'hidden';
        popover.style.opacity = 0;

        window.removeEventListener('mousedown', dismissListener);
    };
}

function atPopover (_pathService_) {
    pathService = _pathService_;

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

atPopover.$inject = [
    'PathService'
];

export default atPopover;
