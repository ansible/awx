describe('Components | panel/body', () => {

    let $compile;
    let $rootScope;

    beforeEach(() => {
        angular.mock.module('at.lib.services')
        angular.mock.module('at.lib.components')
        angular.mock.module('at.test.templates');
    });

    beforeEach(angular.mock.inject((_$compile_, _$rootScope_) => {
        $compile = _$compile_;
        $rootScope = _$rootScope_;
    }));

    it('Should produce at-Panel-body HTML content', () => {
        let element = $compile('<at-panel-body>yo</at-panel-body>')($rootScope);
        $rootScope.$digest();

        expect(element.hasClass('at-Panel-body')).toBe(true);
        expect(element.html()).toContain('yo');
    });
});
