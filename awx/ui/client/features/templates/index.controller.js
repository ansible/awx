function IndexTemplatesController ($scope, strings, dataset) {
    const vm = this;
    vm.strings = strings;
    vm.count = dataset.data.count;

    $scope.$on('updateCount', (e, count) => {
        if (count) {
            vm.count = count;
        }
    });
}

IndexTemplatesController.$inject = [
    '$scope',
    'TemplatesStrings',
    'Dataset'
];

export default IndexTemplatesController;
