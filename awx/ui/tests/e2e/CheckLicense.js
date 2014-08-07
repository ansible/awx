/**********************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * CheckLicense.js
 *
 * Tests the CheckLicense service- helpers/CheckLicense.js
 *
 */

 /* global describe, it, expect, browser */


describe('E2E:CheckLicense', function() {
    it('should present login dialog', function() {
        browser.get('http://localhost:8013');
        var msg = $('#login-modal .login-alert:eq(1)');
        expect(msg.getText()).toMatch(/Please sign in/);

        /*element(by.model('login_username')).sendKeys('admin');
        element(by.model('login_password')).sendKeys('password');
        element(by.id('login-button')).click();*/
    });
});