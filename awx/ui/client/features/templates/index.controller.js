function IndexTemplatesController ($scope, strings, dataset) {
    let vm = this;
    vm.strings = strings;
    vm.count = dataset.data.count;

    $scope.$on('updateDataset', (e, { count }) => {
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
