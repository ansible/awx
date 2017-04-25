describe('Components | panel', () => {
    var $compile,
        $rootScope;

    beforeEach(module('at.components'));

    beforeEach(inject((_$compile_, _$rootScope_) => {
        $compile = _$compile_;
        $rootScope = _$rootScope_;
    }));

    it('should load the navigation partial', function() {
        var element = $compile('<at-panel></at-panel>')($rootScope);

        $rootScope.$digest();
      
        console.log(element.html());
        //expect(element.html()).toContain('<nav class="navbar navbar-default" role="navigation">');
    });
});
