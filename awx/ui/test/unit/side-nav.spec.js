describe('Components | Side Nav', () => {
    let $compile;
    let $rootScope;
    let element;
    let scope;
    let windowMock = {
        innerWidth: 500
    };

    beforeEach(() => {
        angular.mock.module('gettext');
        angular.mock.module('I18N');
        angular.mock.module('ui.router');
        angular.mock.module('at.lib.services')
        angular.mock.module('at.lib.components', ($provide) => {
            $provide.value('$window', windowMock);
        });
    });

    beforeEach(angular.mock.inject((_$compile_, _$rootScope_) => {
        $compile = _$compile_;
        $rootScope = _$rootScope_;
        scope = $rootScope.$new();

        element = angular.element("<at-layout><at-side-nav></at-side-nav><at-layout>");
        element = $compile(element)(scope);
        scope.$digest();
    }));

    describe('Side Nav Controller', () => {
        let sideNav;
        let sideNavCtrl;

        beforeEach(() => {
            sideNav = angular.element(element[0].querySelector('.at-Layout-side'));
            sideNavCtrl = sideNav.controller('atSideNav');
        });

        it('isExpanded defaults to false', () => {
            expect(sideNavCtrl.isExpanded).toBe(false);
        });

        it('toggleExpansion()', () => {
            expect(sideNavCtrl.isExpanded).toBe(false);

            sideNavCtrl.toggleExpansion();
            expect(sideNavCtrl.isExpanded).toBe(true);

            sideNavCtrl.toggleExpansion();
            expect(sideNavCtrl.isExpanded).toBe(false);

            sideNavCtrl.toggleExpansion();
            expect(sideNavCtrl.isExpanded).toBe(true);

            sideNavCtrl.toggleExpansion();
            expect(sideNavCtrl.isExpanded).toBe(false);
        });

        it('isExpanded should be false after state change event', () => {
            sideNavCtrl.isExpanded = true;

            let current = {
                'name': 'dashboard'
            };
            $rootScope.$broadcast('$stateChangeSuccess', current);
            scope.$digest();
            expect(sideNavCtrl.isExpanded).toBe(false);
        });

        it('clickOutsideSideNav watcher should assign isExpanded to false', () => {
            sideNavCtrl.isExpanded = true;

            $rootScope.$broadcast('clickOutsideSideNav');
            scope.$digest();
            expect(sideNavCtrl.isExpanded).toBe(false);
        });
    });
});
