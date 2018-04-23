describe('Components | Side Nav Item', () => {
    let $compile;
    let $rootScope;
    let element;
    let scope;

    beforeEach(() => {
        angular.mock.module('gettext');
        angular.mock.module('I18N');
        angular.mock.module('ui.router');
        angular.mock.module('at.lib.services');
        angular.mock.module('at.lib.components');
        angular.mock.module('Utilities');
        angular.mock.module('ngCookies');
    });

    beforeEach(angular.mock.inject((_$compile_, _$rootScope_) => {
        $compile = _$compile_;
        $rootScope = _$rootScope_;
        scope = $rootScope.$new();

        element = angular.element('<at-layout><at-side-nav><at-side-nav-item icon-class="fa-tachometer" route="dashboard" name="DASHBOARD"></at-side-nav-item></at-layout></at-side-nav>');
        element = $compile(element)(scope);
        scope.name = 'dashboard';
        scope.$digest();
    }));

    describe('Side Nav Item Controller', () => {
        let SideNavItem;
        let SideNavItemCtrl;

        beforeEach(() => {
            SideNavItem = angular.element(element[0].querySelector('at-side-nav-item'));
            SideNavItemCtrl = SideNavItem.controller('atSideNavItem');
        });

        xit('layoutVm.currentState watcher should assign isRoute', () => {
            let current = { name: 'dashboard' };
            $rootScope.$broadcast('$stateChangeSuccess', current);
            scope.$digest();
            expect(SideNavItemCtrl.isRoute).toBe(true);

            current = { name: 'inventories' };
            $rootScope.$broadcast('$stateChangeSuccess', current);
            scope.$digest();
            expect(SideNavItemCtrl.isRoute).toBe(false);
        });

        it('should load name, icon, and route from scope', () => {
            expect(SideNavItem.isolateScope().name).toBeDefined();
            expect(SideNavItem.isolateScope().iconClass).toBeDefined();
            expect(SideNavItem.isolateScope().route).toBeDefined();
        });
    });
});
