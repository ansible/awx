function link (scope, el, attrs, form) {
    scope.form = form.track(el);

    scope.open = false;

    let input = el.find('input')[0];
    let select = el.find('select')[0];

    input.addEventListener('focus', () => select.focus());
    select.addEventListener('focus', () => input.classList.add('at-Input--focus'));

    select.addEventListener('mousedown', () => {
        scope.open = true;
    });

    select.addEventListener('blur', () => {
        input.classList.remove('at-Input--focus');
        scope.open = false;
    });

    select.addEventListener('change', () => {
        scope.open = false;
    });
}

function atInputDropdown () {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: '^^at-form',
        templateUrl: 'static/partials/components/input/dropdown.partial.html',
        link,
        scope: {
            config: '=',
            col: '@'
        }
    };
}

export default atInputDropdown;
