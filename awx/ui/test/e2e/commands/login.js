import { EventEmitter } from 'events';
import { inherits } from 'util';

import {
    AWX_E2E_USERNAME,
    AWX_E2E_PASSWORD,
    AWX_E2E_TIMEOUT_LONG
} from '../settings';

function Login () {
    EventEmitter.call(this);
}

inherits(Login, EventEmitter);

Login.prototype.command = function command (username, password) {
    username = username || AWX_E2E_USERNAME;
    password = password || AWX_E2E_PASSWORD;

    const loginPage = this.api.page.login();

    loginPage
        .navigate()
        .waitForElementVisible('@submit', AWX_E2E_TIMEOUT_LONG)
        .waitForElementNotVisible('div.spinny')
        .setValue('@username', username)
        .setValue('@password', password)
        .click('@submit')
        .waitForElementVisible('div.spinny')
        .waitForElementNotVisible('div.spinny');

    // temporary hack while login issue is resolved
    this.api.elements('css selector', '.LoginModal-alert', result => {
        let alertVisible = false;
        result.value.map(i => i.ELEMENT).forEach(id => {
            this.api.elementIdDisplayed(id, ({ value }) => {
                if (!alertVisible && value) {
                    alertVisible = true;
                    loginPage.setValue('@username', username);
                    loginPage.setValue('@password', password);
                    loginPage.click('@submit');
                    loginPage.waitForElementVisible('div.spinny');
                    loginPage.waitForElementNotVisible('div.spinny');
                }
            });
        });

        this.emit('complete');
    });
};

module.exports = Login;
