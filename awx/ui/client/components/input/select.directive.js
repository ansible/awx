function link (scope, el, attrs, form) {
    form.use(scope, el);

    let input = el.find('input')[0];
    let select = el.find('select')[0];

    input.addEventListener('focus', () => select.focus());
    select.addEventListener('focus', () => input.classList.add('at-Input--focus'));
    select.addEventListener('mousedown', () => scope.open = !scope.open);
    select.addEventListener('change', () => scope.open = false );
    select.addEventListener('blur', () => {
        input.classList.remove('at-Input--focus')
        scope.open = scope.open && false;
    });
}

function atInputSelect (pathService) {
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

atInputSelect.$inject = ['PathService'];

export default atInputSelect;
