describe('Components | Input | File', () => {
    let $scope;
    let element;
    let state;
    let controller;

    const getMockFileEvent = file => ({ target: { files: [file] } });

    beforeEach(() => {
        angular.mock.module('at.lib.services');
        angular.mock.module('at.lib.components');
    });

    describe('AtInputFileController', () => {
        beforeEach(angular.mock.inject(($rootScope, $compile) => {
            const component = '<at-input-file id="unit" state="vm.form.unit"></at-input-file>';
            const dom = angular.element(`<at-form state="vm.form">${component}</at-form>`);

            $scope = $rootScope.$new();
            $scope.vm = { form: { disabled: false, unit: {} } };

            $compile(dom)($scope);
            $scope.$digest();

            element = dom.find('#unit');
            state = $scope.vm.form.unit;
            controller = element.controller('atInputFile');
        }));

        it('should initialize without a value by default', () => {
            expect(state._value).not.toBeDefined();
            expect(state._displayValue).not.toBeDefined();
        });

        it('should update display value with file name when file is read', () => {
            const name = 'notavirus.exe';
            const reader = { result: 'AAAAAAA' };

            controller.check = jasmine.createSpy('check');

            controller.readFile(reader, getMockFileEvent({ name }));

            $scope.$digest();

            expect(state._value).toBeDefined();
            expect(state._displayValue).toEqual(name);

            expect(controller.check).toHaveBeenCalled();
        });

        it('should notify handler on file input change event', () => {
            controller.handleFileChangeEvent = jasmine.createSpy('handleFileChangeEvent');

            element.find('input')[0].dispatchEvent(new Event('change'));

            $scope.$digest();

            expect(controller.handleFileChangeEvent).toHaveBeenCalled();
        });
    });
});
