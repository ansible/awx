let eventService;
let pathService;

function link (scope, el, attrs, form) {
    form.use('input', scope, el);  // avoid passing scope? assign to scope.meta instead or reference form properties in view

    let input = el.find('input')[0];
    let select = el.find('select')[0];

    let listeners = eventService.addListeners(scope, [
        [input, 'focus', () => select.focus()],
        [select, 'mousedown', () => scope.open = !scope.open],
        [select, 'focus', () => input.classList.add('at-Input--focus')],
        [select, 'change', () => scope.open = false],
        [select, 'blur', () => {
            input.classList.remove('at-Input--focus');
            scope.open = scope.open && false;
        }]
    ]);

    scope.$on('$destroy', () => eventService.remove(listeners));

    /*
     * Should notify form on:
     *  - valid (required, passes validation) state change  
     *
     * Should get from form:
     *  - display as disabled
     */
}

function atInputSelect (_eventService_, _pathService_) {
    eventService = _eventService_;
    pathService = _pathService_;

    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: '^^at-form',
        templateUrl: pathService.getPartialPath('components/input/select'),
        link,
        scope: {
            config: '=',
            col: '@'
        }
    };
}

atInputSelect.$inject = [
    'EventService',
    'PathService'
];

export default atInputSelect;
