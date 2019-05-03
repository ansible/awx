const templateUrl = require('~features/credentials/input-source-lookup.partial.html');

function InputSourceLookupController (strings, wait) {
    const vm = this || {};

    vm.strings = strings;
    vm.title = strings.get('inputSources.TITLE');

    vm.$onInit = () => {
        wait('start');
        vm.form.save = () => vm.onTest();
    };

    vm.onReady = () => {
        vm.isReady = true;
        wait('stop');
    };
}

InputSourceLookupController.$inject = [
    'CredentialsStrings',
    'Wait',
];

export default {
    templateUrl,
    controller: InputSourceLookupController,
    controllerAs: 'vm',
    bindings: {
        tabs: '=',
        onClose: '=',
        onNext: '=',
        onSelect: '=',
        onTabSelect: '=',
        onItemSelect: '=',
        onTest: '=',
        selectedId: '=',
        selectedName: '=',
        form: '=',
        resultsFilter: '=',
    },
};
