describe('Components | Layout', () => {
    let $compile;
    let $rootScope;
    let $httpBackend;
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

    beforeEach(angular.mock.inject((_$compile_, _$rootScope_, _$httpBackend_) => {
        $compile = _$compile_;
        $rootScope = _$rootScope_;
        $httpBackend = _$httpBackend_;
        scope = $rootScope.$new();

        element = angular.element('<at-layout></at-layout>');
        element = $compile(element)(scope);
        scope.$digest();
    }));

    describe('AtLayoutController', () => {
        let controller;

        beforeEach(() => {
            const mockOrgAdminResponse = {
                data: {
                    count: 3
                }
            };

            const mockNotificationAdminResponse = {
                data: {
                    count: 1
                }
            };

            controller = element.controller('atLayout');
            $httpBackend.when('GET', /admin_of_organizations/)
                .respond(mockOrgAdminResponse);

            $httpBackend.when('GET', /organizations\/\?role_level=notification_admin_role/)
                .respond(mockNotificationAdminResponse);
        });

        xit('$scope.$on($stateChangeSuccess) should assign toState name to currentState', () => {
            const next = { name: 'dashboard' };
            $rootScope.$broadcast('$stateChangeSuccess', next);
            expect(controller.currentState).toBe('dashboard');
        });

        describe('$root.current_user watcher should assign value to ', () => {
            beforeEach(() => {
                const val = {
                    username: 'admin',
                    id: 1
                };
                $rootScope.current_user = val;
                scope.$digest();
            });

            it('isLoggedIn', () => {
                expect(controller.isLoggedIn).toBe('admin');

                $rootScope.current_user = { id: 1 };
                scope.$digest();
                expect(controller.isLoggedIn).not.toBeDefined();
            });

            it('isSuperUser', () => {
                $rootScope.current_user = 'one';
                $rootScope.user_is_superuser = true;
                $rootScope.user_is_system_auditor = false;
                scope.$digest();
                expect(controller.isSuperUser).toBe(true);

                $rootScope.current_user = 'two';
                $rootScope.user_is_superuser = false;
                $rootScope.user_is_system_auditor = true;
                scope.$digest();
                expect(controller.isSuperUser).toBe(true);

                $rootScope.current_user = 'three';
                $rootScope.user_is_superuser = true;
                $rootScope.user_is_system_auditor = true;
                scope.$digest();
                expect(controller.isSuperUser).toBe(true);

                $rootScope.current_user = 'four';
                $rootScope.user_is_superuser = false;
                $rootScope.user_is_system_auditor = false;
                scope.$digest();
                expect(controller.isSuperUser).toBe(false);
            });

            it('currentUsername', () => {
                expect(controller.currentUsername).toBeTruthy();
                expect(controller.currentUsername).toBe('admin');
            });

            it('currentUserId', () => {
                expect(controller.currentUserId).toBeTruthy();
                expect(controller.currentUserId).toBe(1);
            });
        });

        describe('$root.socketStatus watcher should assign newStatus to', () => {
            const statuses = ['connecting', 'error', 'ok'];

            it('socketState', () => {
                _.forEach(statuses, (status) => {
                    $rootScope.socketStatus = status;
                    scope.$digest();
                    expect(controller.socketState).toBeTruthy();
                    expect(controller.socketState).toBe(status);
                });
            });

            it('socketIconClass', () => {
                _.forEach(statuses, (status) => {
                    $rootScope.socketStatus = status;
                    scope.$digest();
                    expect(controller.socketIconClass).toBe(`icon-socket-${status}`);
                });
            });
        });

        describe('$root.licenseMissing watcher should assign true or false to', () => {
            it('licenseIsMissing', () => {
                $rootScope.licenseMissing = true;
                scope.$digest();
                expect(controller.licenseIsMissing).toBe(true);

                $rootScope.licenseMissing = false;
                scope.$digest();
                expect(controller.licenseIsMissing).toBe(false);
            });
        });

        describe('getString()', () => {
            it('calls ComponentsStrings get() method', angular.mock.inject((_ComponentsStrings_) => {
                spyOn(_ComponentsStrings_, 'get');
                controller.getString('VIEW_DOCS');
                expect(_ComponentsStrings_.get).toHaveBeenCalled();
            }));

            it('ComponentsStrings get() method should return undefined if string is not a property name of the layout class', () => {
                expect(controller.getString('SUBMISSION_ERROR_TITLE')).toBe(undefined);
            });

            it('should return layout string', () => {
                const layoutStrings = {
                    CURRENT_USER_LABEL: 'Logged in as',
                    VIEW_DOCS: 'View Documentation',
                    LOGOUT: 'Logout',
                };

                _.forEach(layoutStrings, (value, key) => {
                    expect(controller.getString(key)).toBe(value);
                });
            });
        });
    });
});
