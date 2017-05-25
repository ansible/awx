function atInputMessage (pathService) {
    return {
        restrict: 'E',
        replace: true,
        templateUrl: pathService.getPartialPath('components/input/message'),
    };
}

atInputMessage.$inject = ['PathService'];

export default atInputMessage;
