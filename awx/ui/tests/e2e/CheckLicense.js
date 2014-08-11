/**********************************
 * Copyright (c) 2014 AnsibleWorks, Inc.
 *
 * CheckLicense.js
 *
 * Tests the CheckLicense service- helpers/CheckLicense.js
 *
 */

 /* global describe, it, expect, by, browser, element, beforeEach */


describe('E2E:CheckLicense', function() {
    beforeEach(function() {
        browser.get('http://localhost:8013');
    });

    it('should present login dialog', function() {
        var msg = element.all(by.css('#login-modal .login-alert'));
        expect(msg.get(0).getText()).toMatch(/Please sign in/);
    });

    it('should login', function() {
        element(by.model('login_username')).sendKeys('admin');
        element(by.model('login_password')).sendKeys('password01!');
        element(by.id('login-button')).click();
    });
});