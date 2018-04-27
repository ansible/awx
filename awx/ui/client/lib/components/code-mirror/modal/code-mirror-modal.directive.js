const templateUrl = require('~components/code-mirror/modal/code-mirror-modal.partial.html');

const CodeMirrorModalID = '#CodeMirror-modal';
const CodeMirrorID = 'codemirror-extra-vars-modal';
const ParseVariable = 'parseType';
const CodeMirrorVar = 'extra_variables';
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

    function resize () {
        const editor = $(`${CodeMirrorModalID} .CodeMirror`)[0].CodeMirror;
        const height = $(ModalHeight).height() - $(ModalHeader).height() -
            $(ModalFooter).height() - 100;
        editor.setSize('100%', height);
    }

    function toggle () {
        $scope.parseTypeChange('parseType', 'extra_variables');
        setTimeout(resize, 0);
    }

    function init () {
        $(CodeMirrorModalID).modal('show');
        $scope.extra_variables = ParseVariableString(_.cloneDeep($scope.variables));
        $scope.parseType = ParseType;
        const options = {
            scope: $scope,
            variable: CodeMirrorVar,
            parse_variable: ParseVariable,
            field_id: CodeMirrorID,
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

    vm.strings = strings;
    vm.toggle = toggle;
    init();
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
            closeFn: '&'
        }
    };
}

export default atCodeMirrorModal;
