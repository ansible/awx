function IndexTemplatesController (strings, dataset) {
    let vm = this;
    vm.strings = strings;
    vm.count = dataset.data.count;
}

IndexTemplatesController.$inject = [
    'TemplatesStrings',
    'Dataset'
];

export default IndexTemplatesController;
