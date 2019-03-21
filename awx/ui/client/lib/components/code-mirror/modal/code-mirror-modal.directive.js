const templateUrl = require('~components/code-mirror/modal/code-mirror-modal.partial.html');

const CodeMirrorModalID = '#CodeMirror-modal';
const ParseVariable = 'parseType';
const ParseType = 'yaml';
const ModalHeight = '#CodeMirror-modal .modal-dialog';
const ModalHeader = '.atCodeMirror-label';
const ModalFooter = '.CodeMirror-modalControls';

function atCodeMirrorModalController (
    $scope,
    strings,
    ParseTypeChange,
    ParseVariableString
) {
    const vm = this;
    const variables = `${$scope.name}_variables`;
    function resize () {
        if ($scope.disabled === 'true') {
            $scope.disabled = true;
        } else if ($scope.disabled === 'false') {
            $scope.disabled = false;
        }
        const editor = $(`${CodeMirrorModalID} .CodeMirror`)[0].CodeMirror;
        const height = $(ModalHeight).height() - $(ModalHeader).height() -
            $(ModalFooter).height() - 100;
        editor.setSize('100%', height);
    }

    function toggle () {
        $scope.parseTypeChange('parseType', variables);
        setTimeout(resize, 0);
    }

    function init (vars, name) {
        if ($scope.disabled === 'true') {
            $scope.disabled = true;
        } else if ($scope.disabled === 'false') {
            $scope.disabled = false;
        }
        $(CodeMirrorModalID).modal('show');
        $scope[variables] = ParseVariableString(_.cloneDeep(vars));
        $scope.parseType = ParseType;
        const options = {
            scope: $scope,
            variable: variables,
            parse_variable: ParseVariable,
            field_id: name,
            readOnly: $scope.disabled
        };
        ParseTypeChange(options);
        resize();
        $(CodeMirrorModalID).on('hidden.bs.modal', $scope.closeFn);
        $(`${CodeMirrorModalID} .modal-dialog`).resizable({
            minHeight: 523,
            minWidth: 600
        });
        $(`${CodeMirrorModalID} .modal-dialog`).on('resize', resize);
    }

    vm.variables = variables;
    vm.name = $scope.name;
    vm.strings = strings;
    vm.toggle = toggle;
    if ($scope.init) {
        $scope.init = init;
    }
    angular.element(document).ready(() => {
        init($scope.variables, $scope.name);
    });
}

atCodeMirrorModalController.$inject = [
    '$scope',
    'CodeMirrorStrings',
    'ParseTypeChange',
    'ParseVariableString',
];

function atCodeMirrorModal () {
    return {
        restrict: 'E',
        replace: true,
        transclude: true,
        templateUrl,
        controller: atCodeMirrorModalController,
        controllerAs: 'vm',
        scope: {
            disabled: '@',
            label: '@',
            labelClass: '@',
            tooltip: '@',
            variables: '@',
            name: '@',
            closeFn: '&'
        }
    };
}

export default atCodeMirrorModal;
