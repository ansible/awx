/**********************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * CheckLicense.js
 *
 * Tests the CheckLicense service- helpers/CheckLicense.js
 *
 */

describe('Unit:CheckLicense', function() {

    var scope;

    beforeEach(module('Tower'));

    beforeEach(inject(function($rootScope) {
        scope = $rootScope.$new();
    }));

    it('should contain CheckLicense service', inject(function(CheckLicense) {
        expect(CheckLicense).not.toBe(null);
    }));

    it('should have a getRemainingDays method', inject(function(CheckLicense) {
        expect(CheckLicense.getRemainingDays).not.toBe(null);
    }));

});
