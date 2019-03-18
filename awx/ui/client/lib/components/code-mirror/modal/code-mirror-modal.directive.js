const templateUrl = require('~components/code-mirror/modal/code-mirror-modal.partial.html');

const CodeMirrorModalID = '#CodeMirror-modal';
// const ParseVariable = 'parseType';
const ParseType = 'yaml';
const ModalHeight = '#CodeMirror-modal .modal-dialog';
const ModalHeader = '.atCodeMirror-label';
const ModalFooter = '.CodeMirror-modalControls';

function atCodeMirrorModalController (
    $scope,
    strings,
    ParseTypeChange
) {
    const vm = this;
    // const variablesName = `${$scope.name}_variables`;
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
        $scope.parseTypeChange('parseType', 'modalVars');
        setTimeout(resize, 0);
    }

    function init () {
        if ($scope.disabled === 'true') {
            $scope.disabled = true;
        } else if ($scope.disabled === 'false') {
            $scope.disabled = false;
        }
        $(CodeMirrorModalID).modal('show');
        $scope.parseType = ParseType;
        ParseTypeChange({
            scope: $scope,
            variable: 'modalVars',
            parse_variable: 'parseType',
            field_id: 'variables_modal',
            readOnly: $scope.disabled
        });
        resize();
        $(CodeMirrorModalID).on('hidden.bs.modal', $scope.closeFn);
        $(`${CodeMirrorModalID} .modal-dialog`).resizable({
            minHeight: 523,
            minWidth: 600
        });
        $(`${CodeMirrorModalID} .modal-dialog`).on('resize', resize);
    }

    vm.strings = strings;
    vm.toggle = toggle;
    $scope.close = () => {
        $scope.closeFn({
            values: $scope.modalVars,
            parseType: $scope.parseType,
        });
    };
    if ($scope.init) {
        $scope.init = init;
    }
    angular.element(document).ready(() => {
        init($scope.variablesName, $scope.name);
    });
}

atCodeMirrorModalController.$inject = [
    '$scope',
    'CodeMirrorStrings',
    'ParseTypeChange',
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
            modalVars: '=',
            parseType: '=',
            name: '@',
            closeFn: '&'
        }
    };
}

export default atCodeMirrorModal;
