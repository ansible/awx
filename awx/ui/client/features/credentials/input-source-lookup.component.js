const templateUrl = require('~features/credentials/input-source-lookup.partial.html');

function InputSourceLookupController ($scope, $element, $http, GetBasePath, qs, strings) {
    const vm = this || {};
    let overlay;

    vm.strings = strings;
    vm.name = 'credential';
    vm.title = 'Set Input Source';

    vm.$onInit = () => {
        const [el] = $element;
        overlay = el.querySelector('#input-source-lookup');

        const defaultParams = {
            order_by: 'name',
            credential_type__kind: 'external',
            page_size: 5
        };
        vm.setDefaultParams(defaultParams);
        vm.setData({ results: [], count: 0 });
        $http({ method: 'GET', url: GetBasePath(`${vm.name}s`), params: defaultParams })
            .then(({ data }) => {
                vm.setData(data);
                vm.show();
            });
    };

    vm.show = () => {
        overlay.style.display = 'block';
        overlay.style.opacity = 1;
    };

    vm.close = () => {
        vm.onClose();
    };

    vm.next = () => {
        vm.onNext();
    };

    vm.select = () => {
        vm.onSelect();
    };

    vm.test = () => {
        vm.onTest();
    };

    vm.setData = ({ results, count }) => {
        vm.dataset = { results, count };
        vm.collection = vm.dataset.results;
    };

    vm.setDefaultParams = (params) => {
        vm.list = { name: vm.name, iterator: vm.name };
        vm.defaultParams = params;
        vm.queryset = params;
    };

    vm.toggle_row = (obj) => {
        vm.onRowClick(obj);
    };

    vm.onCredentialTabClick = () => vm.onTabSelect('credential');
}

InputSourceLookupController.$inject = [
    '$scope',
    '$element',
    '$http',
    'GetBasePath',
    'QuerySet',
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
    },
};
