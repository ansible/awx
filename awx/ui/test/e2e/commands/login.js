import { EventEmitter } from 'events';
import { inherits } from 'util';


const Login = function() {
    EventEmitter.call(this);
}

inherits(Login, EventEmitter);


Login.prototype.command = function(username, password) {

    username = username || this.api.globals.awxUsername;
    password = password || this.api.globals.awxPassword;

    const loginPage = this.api.page.login();

    loginPage
        .navigate()
        .waitForElementVisible('@submit', this.api.globals.longWait)
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
                    loginPage.setValue('@username', username)
                    loginPage.setValue('@password', password)
                    loginPage.click('@submit')
                    loginPage.waitForElementVisible('div.spinny')
                    loginPage.waitForElementNotVisible('div.spinny');
                }
            })
        })
        this.emit('complete');
    })
};

module.exports = Login;
