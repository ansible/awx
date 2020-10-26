'use strict';

describe('Controller: LicenseController', () => {
    // Setup
    let scope,
        LicenseController,
        ConfigService,
        ProcessErrors,
        config,
        subscriptionCreds;

    beforeEach(angular.mock.module('awApp'));
    beforeEach(angular.mock.module('license', ($provide) => {
        ConfigService = jasmine.createSpyObj('ConfigService', [
            'getConfig',
            'delete'
            ]);

        config = {
            license_info: {
                time_remaining: 1234567 // seconds
            },
            version: '3.1.0-devel'
        };

        subscriptionCreds = {
            password: '$encrypted$',
            username: 'foo',
        }

        ProcessErrors = jasmine.createSpy('ProcessErrors');

        $provide.value('ConfigService', ConfigService);
        $provide.value('ProcessErrors', ProcessErrors);
        $provide.value('config', config);
        $provide.value('subscriptionCreds', subscriptionCreds);
    }));

    beforeEach(angular.mock.inject( ($rootScope, $controller, _ConfigService_, _ProcessErrors_, _config_, _subscriptionCreds_) => {
        scope = $rootScope.$new();
        ConfigService = _ConfigService_;
        ProcessErrors = _ProcessErrors_;
        config = _config_;
        subscriptionCreds = _subscriptionCreds_;
        LicenseController = $controller('licenseController', {
            $scope: scope,
            ConfigService: ConfigService,
            ProcessErrors: ProcessErrors,
            config: config,
            subscriptionCreds: subscriptionCreds
        });
    }));

    xit('should show correct expiration date', ()=>{
        let date = new Date(),
            options = {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            };
        date.setDate(date.getDate() + 14);
        expect(scope.time.expiresOn).toEqual(date.toLocaleDateString(undefined, options));
    });

    it('should show correct time remaining', ()=>{
        expect(scope.time.remaining).toMatch('14 Days');
    });

    xit('should throw an error if provided license is invalid JSON', ()=>{
        let event = {
            target: {files: [new File(['asdf'], 'license.txt', {type: 'text/html'})]}
        };
        scope.getKey(event);
        expect(ProcessErrors).toHaveBeenCalled();
    });

    xit('should submit a valid license');
});
