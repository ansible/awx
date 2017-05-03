function link (scope, el, attrs, form) {
    scope.form = form.track(el);
    console.log('text', scope.form);
}

function atInputText () {
    return {
        restrict: 'E',
        transclude: true,
        replace: true,
        require: '^^at-form',
        templateUrl: 'static/partials/components/input/text.partial.html',
        link,
        scope: {
            config: '=',
            col: '@'
        }
    };
}

export default atInputText;
