import defaultStrings from '~assets/default.strings.json';

export default [ '$state',
    function ($state) {
        const vm = this;

        vm.product = defaultStrings.BRAND_NAME;      

        vm.goToCard = (card) => {
            $state.go('settings.form', { form: card });
        };
    }
];
