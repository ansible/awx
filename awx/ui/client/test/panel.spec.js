describe('Components | panel', () => {

    let $compile;
    let $rootScope;

    beforeEach(done => {
        angular.mock.module('at.components')
        angular.mock.module('at.test.templates');

        inject((_$compile_, _$rootScope_) => {
            $compile = _$compile_;
            $rootScope = _$rootScope_;
            done();
        });
    });

    it('should load the navigation partial', function() {
        var element = $compile('<at-panel></at-panel>')($rootScope);
        $rootScope.$digest();
      
        expect(element.html()).toContain('at-Panel');
    }); });
