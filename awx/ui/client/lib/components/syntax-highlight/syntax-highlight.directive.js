const templateUrl = require('~components/syntax-highlight/syntax-highlight.partial.html');

function atSyntaxHighlightController ($scope, AngularCodeMirror) {
    const vm = this;
    const variablesName = `${$scope.name}_codemirror`;

    function init () {
        if ($scope.disabled === 'true') {
            $scope.disabled = true;
        } else if ($scope.disabled === 'false') {
            $scope.disabled = false;
        }
        // TODO: get default value
        $scope.value = $scope.value || $scope.default;
        $scope.parseType = 'jinja2';

        $scope.variablesName = variablesName;
        $scope[variablesName] = $scope.value || '';
        const codeMirror = AngularCodeMirror($scope.disabled);
        codeMirror.addModes({
            jinja2: {
                mode: 'jinja2',
                matchBrackets: true,
                autoCloseBrackets: true,
                styleActiveLine: true,
                lineNumbers: true,
                gutters: ['CodeMirror-lint-markers'],
                lint: true,
                scrollbarStyle: null,
            }
        });
        codeMirror.showTextArea({
            scope: $scope,
            model: variablesName,
            element: `${$scope.name}_codemirror`,
            lineNumbers: true,
            mode: 'jinja2',
        });

        $scope.$watch(variablesName, () => {
            $scope.value = $scope[variablesName];
        });
    }

    vm.name = $scope.name;
    // vm.variablesName = variablesName;
    vm.parseType = $scope.parseType;
    if ($scope.init) {
        $scope.init = init;
    }
    angular.element(document).ready(() => {
        init();
    });
}

atSyntaxHighlightController.$inject = [
    '$scope',
    'AngularCodeMirror'
];

function atCodeMirrorTextarea () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl,
        controller: atSyntaxHighlightController,
        controllerAs: 'vm',
        scope: {
            disabled: '@',
            label: '@',
            labelClass: '@',
            tooltip: '@',
            tooltipPlacement: '@',
            value: '=',
            name: '@',
            init: '='
        }
    };
}

export default atCodeMirrorTextarea;
