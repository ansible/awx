describe('Components | Layout', () => {
    let $compile;
    let $rootScope;
    let element;
    let scope;

    beforeEach(() => {
        angular.mock.module('gettext');
        angular.mock.module('I18N');
        angular.mock.module('ui.router');
        angular.mock.module('at.lib.services')
        angular.mock.module('at.lib.components')
    });

    beforeEach(angular.mock.inject((_$compile_, _$rootScope_) => {
        $compile = _$compile_;
        $rootScope = _$rootScope_;
        scope = $rootScope.$new();

        element = angular.element('<at-layout></at-layout>');
        element = $compile(element)(scope);
        scope.$digest();
    }));

    describe('AtLayoutController', () => {
        let controller;

        beforeEach(()=> {
            controller = element.controller('atLayout');
        });

        it('$scope.$on($stateChangeSuccess) should assign toState name to currentState', () => {
            let next = {'name': 'dashboard'};
            $rootScope.$broadcast('$stateChangeSuccess', next);
            expect(controller.currentState).toBe('dashboard');
        });

        describe('$root.current_user watcher should assign value to ', () => {
            beforeEach(() => {
                let val = {
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
            let statuses = ['connecting', 'error', 'ok'];

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
            it('should return layout string', () => {
                let layoutStrings = {
                    CURRENT_USER_LABEL: 'Logged in as',
                    VIEW_DOCS: 'View Documentation',
                    LOGOUT: 'Logout',
                    DASHBOARD: 'Dashboard',
                    JOBS: 'Jobs',
                    SCHEDULES: 'Schedules',
                    PORTAL_MODE: 'Portal Mode',
                    PROJECTS: 'Projects',
                    CREDENTIALS: 'Credentials',
                    CREDENTIAL_TYPES: 'Credential Types',
                    INVENTORIES: 'Inventories',
                    TEMPLATES: 'Templates',
                    ORGANIZATIONS: 'Organizations',
                    USERS: 'Users',
                    TEAMS: 'Teams',
                    INVENTORY_SCRIPTS: 'Inventory Scripts',
                    NOTIFICATIONS: 'Notifications',
                    MANAGEMENT_JOBS: 'Management Jobs',
                    INSTANCE_GROUPS: 'Instance Groups',
                    SETTINGS: 'Settings',
                    FOOTER_ABOUT: 'About',
                    FOOTER_COPYRIGHT: 'Copyright © 2017 Red Hat, Inc.'
                };

                _.forEach(layoutStrings, (value, key) => {
                    expect(controller.getString(key)).toBe(value);
                });
            });

            it('should return default string', () => {
                let defaultStrings = {
                    BRAND_NAME: "AWX"
                };

                _.forEach(defaultStrings, (value, key) => {
                    expect(controller.getString(key)).toBe(value);
                });
            });
        });
    });
});