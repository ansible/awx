const templateUrl = require('~features/credentials/input-source-lookup.partial.html');

function InputSourceLookupController (strings) {
    const vm = this || {};

    vm.strings = strings;
    vm.title = strings.get('inputSources.TITLE');
}

InputSourceLookupController.$inject = [
    'CredentialsStrings',
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
        onRowClick: '=',
        onTest: '=',
        selectedId: '=',
        form: '=',
        resultsFilter: '=',
    },
};
