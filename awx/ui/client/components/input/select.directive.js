let eventService;
let pathService;

function link (scope, el, attrs, form) {
    form.use(scope, el);

    let apply = eventService.listenWith(scope);

    let input = el.find('input')[0];
    let select = el.find('select')[0];

    input.addEventListener('focus', apply(select.focus));
    select.addEventListener('mousedown', apply(() => scope.open = !scope.open));
    select.addEventListener('change', () => apply(() => scope.open = false));
    select.addEventListener('focus', apply(() => input.classList.add('at-Input--focus')));

    select.addEventListener('blur', apply(() => {
        input.classList.remove('at-Input--focus');
        scope.open = scope.open && false;
    }));
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
