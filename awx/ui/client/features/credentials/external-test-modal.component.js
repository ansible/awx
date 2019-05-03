const templateUrl = require('~features/credentials/external-test-modal.partial.html');

function ExternalTestModalController (strings) {
    const vm = this || {};

    vm.strings = strings;
    vm.title = strings.get('externalTest.TITLE');

    vm.$onInit = () => {
        vm.form.save = () => vm.onSubmit();
    };
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
