'use strict';

describe('Controller: LicenseController', () => {
    // Setup
    let scope,
        LicenseController,
        ConfigService,
        ProcessErrors;

    beforeEach(angular.mock.module('Tower'));
    beforeEach(angular.mock.module('license', ($provide) => {
        ConfigService = jasmine.createSpyObj('ConfigService', [
            'getConfig',
            'delete'
            ]);

        ConfigService.getConfig.and.returnValue({
            then: function(callback){
                return callback({
                    license_info: {
                        time_remaining: 1234567 // seconds
                    },
                    version: '3.1.0-devel'
                });
            }
        });

        ProcessErrors = jasmine.createSpy('ProcessErrors');

        $provide.value('ConfigService', ConfigService);
        $provide.value('ProcessErrors', ProcessErrors);
    }));

    beforeEach(angular.mock.inject( ($rootScope, $controller, _ConfigService_, _ProcessErrors_) => {
        scope = $rootScope.$new();
        ConfigService = _ConfigService_;
        ProcessErrors = _ProcessErrors_;
        LicenseController = $controller('licenseController', {
            $scope: scope,
            ConfigService: ConfigService,
            ProcessErrors: ProcessErrors
        });
    }));

    // Suites
    it('should GET a config object on initialization', ()=>{
        expect(ConfigService.getConfig).toHaveBeenCalled();
    });

    it('should show correct expiration date', ()=>{
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
