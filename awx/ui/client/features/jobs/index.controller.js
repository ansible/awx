function IndexJobsController ($scope, strings, dataset) {
    const vm = this;
    vm.strings = strings;
    vm.count = dataset.data.count;

    $scope.$on('updateDataset', (e, { count }) => {
        if (count) {
            vm.count = count;
        }
    });
}

IndexJobsController.$inject = [
    '$scope',
    'JobsStrings',
    'Dataset'
];

export default IndexJobsController;
