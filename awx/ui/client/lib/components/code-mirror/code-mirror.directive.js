const templateUrl = require('~components/code-mirror/code-mirror.partial.html');

const CodeMirrorID = 'codemirror-extra-vars';
const CodeMirrorModalID = '#CodeMirror-modal';
const ParseVariable = 'parseType';
const CodeMirrorVar = 'variables';
const ParseType = 'yaml';

function atCodeMirrorController (
    $scope,
    strings,
    ParseTypeChange,
    ParseVariableString
) {
    const vm = this;

    function init (vars) {
        $scope.variables = ParseVariableString(_.cloneDeep(vars));
        $scope.parseType = ParseType;
        const options = {
            scope: $scope,
            variable: CodeMirrorVar,
            parse_variable: ParseVariable,
            field_id: CodeMirrorID,
            readOnly: $scope.disabled
        };
        ParseTypeChange(options);
    }

    function expand () {
        vm.expanded = true;
    }

    function close () {
        $(CodeMirrorModalID).off('hidden.bs.modal');
        $(CodeMirrorModalID).modal('hide');
        $('.popover').popover('hide');
        vm.expanded = false;
    }

    vm.strings = strings;
    vm.expanded = false;
    vm.close = close;
    vm.expand = expand;
    if ($scope.init) {
        $scope.init = init;
    }
    init($scope.variables);
}

atCodeMirrorController.$inject = [
    '$scope',
    'CodeMirrorStrings',
    'ParseTypeChange',
    'ParseVariableString'
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
            variables: '@',
            init: '='
        }
    };
}

export default atCodeMirrorTextarea;
