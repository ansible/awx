/**********************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * CheckLicense.js
 *
 * Tests the CheckLicense service- helpers/CheckLicense.js
 *
 */

 /* global describe, it, beforeEach, expect, module, inject */

 var licenses = [{
        desc: 'expired license with < 1 day grace period',
        valid_key: true,
        time_remaining: 0,
        grace_period_remaining: 85000,
        free_instances: 10,
        expects: 'grace period has been exceeded'
    }, {
        desc: 'expired license with > 1 day grace period',
        valid_key: true,
        time_remaining: 0,
        grace_period_remaining: (86400 * 2),
        free_instances: 10,
        expects: 'after 2 days'
    }, {
        desc: 'valid license with time remaining = 15 days',
        valid_key: true,
        time_remaining: (86400 * 15),
        grace_period_remaining: 0,
        free_instances: 10,
        expects: 'license is valid'
    }, {
        desc: 'valid license with time remaining < 15 days',
        valid_key: true,
        time_remaining: (86400 * 10) ,
        grace_period_remaining: 0,
        free_instances: 10,
        expects: 'license has 10 days remaining'
    }, {
        desc: 'valid license with time remaining > 15 days and remaining hosts > 0',
        valid_key: true,
        time_remaining: (86400 * 20),
        free_instances: 10,
        grace_period_remaining: 0,
        expects: 'license is valid'
    }, {
        desc: 'valid license with time remaining > 15 days and remaining hosts = 0',
        valid_key: true,
        time_remaining: (86400 * 20) ,
        grace_period_remaining: 0,
        free_instances: 0,
        expects: 'license has reached capacity'
    }];

describe('Unit:CheckLicense', function() {

    beforeEach(module('Tower'));

    /*beforeEach(inject(function($rootScope) {
        scope = $rootScope.$new();
    }));*/

    it('should contain CheckLicense service', inject(function(CheckLicense) {
        expect(CheckLicense).not.toBe(null);
    }));

    it('should have a getRemainingDays method', inject(function(CheckLicense) {
        expect(CheckLicense.getRemainingDays).not.toBe(null);
    }));

    it('should have a getHTML method', inject(function(CheckLicense) {
        expect(CheckLicense.getHTML).not.toBe(null);
    }));

    it('should have a getAdmin method', inject(function(CheckLicense) {
        expect(CheckLicense.getAdmin).not.toBe(null);
    }));

    licenses.forEach(function(lic) {
        it(lic.desc, inject(function(CheckLicense) {
            var r = new RegExp(lic.expects);
            expect(CheckLicense.getHTML(lic).body).toMatch(r);
        }));
    });

    it('should recognize empty license as invalid', inject(function(CheckLicense) {
        expect(CheckLicense.getHTML({}).title).toMatch(/license required/i);
    }));

    it('should show license update form to admin users when license is invalid', inject(function(CheckLicense, $rootScope) {
        $rootScope.current_user = {};
        $rootScope.current_user.is_superuser = true;
        expect(CheckLicense.getHTML({}).body).toMatch(/license\_license\_json/);
    }));

    it('should not show license update form to non-admin users when license is invalid', inject(function(CheckLicense, $rootScope) {
        $rootScope.current_user = {};
        $rootScope.current_user.is_superuser = false;
        expect(CheckLicense.getHTML({}).body).not.toMatch(/license\_license\_json/);
    }));
});
