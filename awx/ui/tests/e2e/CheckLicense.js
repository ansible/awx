/**********************************
 * Copyright (c) 2015 Ansible, Inc.
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
        var labels = element.all(by.css('#login-modal .modal-body label'));
        expect(labels.get(0).getText()).toMatch(/Username/);
    });

    it('should login', function() {
        element(by.model('login_username')).sendKeys('admin');
        element(by.model('login_password')).sendKeys('password01!');
        element(by.id('login-button')).click();
        var user = element(by.css('#account-menu [ng-bind="current_user.username"]'));
        expect(user.getText()).toMatch(/admin/);
    });
});