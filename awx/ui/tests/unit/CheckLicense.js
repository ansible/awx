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
        expects: '2 grace days'
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
    }, {
        desc: 'expired trial license with > 1 day grace period',
        valid_key: true,
        trial: true,
        time_remaining: 0,
        grace_period_remaining: (86400 * 2),
        free_instances: 10,
        notExpects: 'grace days'
    } , {
        desc: 'expired trial license with < 1 day grace period',
        valid_key: true,
        trial: true,
        time_remaining: 0,
        grace_period_remaining: 0,
        free_instances: 10,
        notExpects: '30 day grace period'
    }, {
        desc: 'trial license with time remaining = 15 days',
        trial: true,
        valid_key: true,
        time_remaining: (86400 * 15),
        grace_period_remaining: 0,
        free_instances: 10,
        notExpects: 'grace period'
    }, {
        desc: 'trial license with time remaining < 15 days',
        valid_key: true,
        trial: true,
        time_remaining: (86400 * 10) ,
        grace_period_remaining: 0,
        free_instances: 10,
        notExpects: 'grace period'
    }];

var should_notify = [{
        desc: 'should notify when license expired',
        valid_key: true,
        time_remaining: 0,
        grace_period_remaining: 85000,
        free_instances: 10
    }, {
        desc: 'should notify when license time remaining < 15 days',
        valid_key: true,
        time_remaining: (86400 * 10) ,
        grace_period_remaining: 0,
        free_instances: 10
    }, {
        desc: 'should notify when host count <= 0',
        valid_key: true,
        time_remaining: (86400 * 200) ,
        grace_period_remaining: 0,
        free_instances: 0
    }, {
        desc: 'should notify when license is invalid',
        valid_key: false
    },{
        desc: 'should notify when license is empty',
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

    it('should have a shouldNotify method', inject(function(CheckLicense) {
        expect(CheckLicense.shouldNotify).not.toBe(null);
    }));

    it('should not notify when license valid, time remaining > 15 days and host count > 0', inject(function(CheckLicense) {
        expect(CheckLicense.shouldNotify({
            valid_key: true,
            time_remaining: (86400 * 20),
            grace_period_remaining: 0,
            free_instances: 10 })).toBe(false);
    }));

    should_notify.forEach(function(lic) {
        it(lic.desc, inject(function(CheckLicense) {
            expect(CheckLicense.shouldNotify(lic)).toBe(true);
        }));
    });

    licenses.forEach(function(lic) {
        it(lic.desc, inject(function(CheckLicense) {
            var r;
            if (lic.expects) {
                r = new RegExp(lic.expects);
                expect(CheckLicense.getHTML(lic).body).toMatch(r);
            } else {
                r = new RegExp(lic.notExpects);
                expect(CheckLicense.getHTML(lic).body).not.toMatch(r);
            }
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
