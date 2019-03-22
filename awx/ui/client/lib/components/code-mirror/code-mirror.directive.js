const templateUrl = require('~components/code-mirror/code-mirror.partial.html');

const CodeMirrorModalID = '#CodeMirror-modal';

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
        $scope.variables = sanitizeVars($scope.variables);
        $scope.parseType = 'yaml';

        $scope.variablesName = variablesName;
        $scope[variablesName] = $scope.variables;
        ParseTypeChange({
            scope: $scope,
            variable: variablesName,
            parse_variable: 'parseType',
            field_id: `${$scope.name}_variables`,
            readOnly: $scope.disabled
        });

        $scope.$watch(variablesName, () => {
            $scope.variables = $scope[variablesName];
        });
    }

    function expand () {
        vm.expanded = true;
    }

    function close (varsFromModal, parseTypeFromModal) {
        $scope.variables = varsFromModal;
        $scope[variablesName] = $scope.variables;
        $scope.parseType = parseTypeFromModal;
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

    // Adding this function b/c sometimes extra vars are returned to the
    // UI as yaml (ex: "foo: bar"), and other times as a
    // json-object-string (ex: "{"foo": "bar"}"). The latter typically
    // occurs when host vars were system generated and not user-input
    // (such as adding a cloud host);
    function sanitizeVars (str) {
        // Quick function to test if the host vars are a json-object-string,
        // by testing if they can be converted to a JSON object w/o error.
        function IsJsonString (varStr) {
            try {
                JSON.parse(varStr);
            } catch (e) {
                return false;
            }
            return true;
        }

        if (typeof str === 'undefined') {
            return '---';
        }
        if (typeof str !== 'string') {
            const yamlStr = jsyaml.safeDump(str);
            // jsyaml.safeDump doesn't process an empty object correctly
            if (yamlStr === '{}\n') {
                return '---';
            }
            return yamlStr;
        }
        if (str === '' || str === '{}') {
            return '---';
        } else if (IsJsonString(str)) {
            str = JSON.parse(str);
            return jsyaml.safeDump(str);
        }
        return str;
    }

    vm.name = $scope.name;
    vm.strings = strings;
    vm.expanded = false;
    vm.close = close;
    vm.expand = expand;
    vm.variablesName = variablesName;
    vm.parseType = $scope.parseType;
    if ($scope.init) {
        $scope.init = init;
    }
    angular.element(document).ready(() => {
        init();
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
