const templateUrl = require('~components/code-mirror/code-mirror.partial.html');

const CodeMirrorModalID = '#CodeMirror-modal';
const ParseType = 'yaml';

function atCodeMirrorController (
    $scope,
    strings,
    ParseTypeChange
) {
    const vm = this;
    const variablesName = `${$scope.name}_variables`;
    function init () {
        if ($scope.disabled === 'true') {
            $scope.disabled = true;
        } else if ($scope.disabled === 'false') {
            $scope.disabled = false;
        }
        $scope.parseType = ParseType;

        $scope[variablesName] = $scope.variables;
        ParseTypeChange({
            scope: $scope,
            variable: variablesName,
            parse_variable: 'parseType',
            field_id: `${$scope.name}_variables`,
            readOnly: $scope.disabled
        });
    }

    function expand () {
        vm.expanded = true;
    }

    function close (varsFromModal) {
        // TODO: make sure that the variables format matches
        // parseType before re-initializing CodeMirror.  Ex)
        // user changes the format from yaml to json in the
        // modal but CM in the form is set to YAML
        $scope.variables = varsFromModal;
        $scope[variablesName] = $scope.variables;
        // New set of variables from the modal, reinit codemirror
        ParseTypeChange({
            scope: $scope,
            variable: variablesName,
            parse_variable: 'parseType',
            field_id: `${$scope.name}_variables`,
            readOnly: $scope.disabled
        });
        $(CodeMirrorModalID).off('hidden.bs.modal');
        $(CodeMirrorModalID).modal('hide');
        $('.popover').popover('hide');
        vm.expanded = false;
    }

    vm.name = $scope.name;
    vm.strings = strings;
    vm.expanded = false;
    vm.close = close;
    vm.expand = expand;
    vm.variablesName = variablesName;
    if ($scope.init) {
        $scope.init = init;
    }
    angular.element(document).ready(() => {
        init($scope.variables, $scope.name);
    });
}

atCodeMirrorController.$inject = [
    '$scope',
    'CodeMirrorStrings',
    'ParseTypeChange'
];

function atCodeMirrorTextarea () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl,
        controller: atCodeMirrorController,
        controllerAs: 'vm',
        scope: {
            disabled: '@',
            label: '@',
            labelClass: '@',
            tooltip: '@',
            tooltipPlacement: '@',
            variables: '=',
            name: '@',
            init: '='
        }
    };
}

export default atCodeMirrorTextarea;
