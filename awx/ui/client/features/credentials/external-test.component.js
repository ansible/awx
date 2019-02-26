const templateUrl = require('~features/credentials/external-test.partial.html');

function ExternalTestModalController ($scope, $element, strings) {
    const vm = this || {};
    let overlay;

    vm.strings = strings;
    vm.title = 'Test External Credential';

    vm.$onInit = () => {
        const [el] = $element;
        overlay = el.querySelector('#external-test-modal');
        vm.show();
    };

    vm.show = () => {
        overlay.style.display = 'block';
        overlay.style.opacity = 1;
    };
}

ExternalTestModalController.$inject = [
    '$scope',
    '$element',
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
