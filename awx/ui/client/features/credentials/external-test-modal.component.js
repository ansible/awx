const templateUrl = require('~features/credentials/external-test-modal.partial.html');

function ExternalTestModalController (strings) {
    const vm = this || {};

    vm.strings = strings;
    vm.title = strings.get('externalTest.TITLE');
}

ExternalTestModalController.$inject = [
    'CredentialsStrings',
];

export default {
    templateUrl,
    controller: ExternalTestModalController,
    controllerAs: 'vm',
    bindings: {
        onClose: '=',
        onSubmit: '=',
        form: '=',
    },
};
