function IndexJobsController ($scope, strings, dataset) {
    const vm = this;
    vm.strings = strings;
    vm.count = dataset.data.count;

    $scope.$on('updateCount', (e, count) => {
        if (typeof count === 'number') {
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
