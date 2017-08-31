import { EventEmitter } from 'events';
import { inherits } from 'util';


const Login = function() {
    EventEmitter.call(this);
}

inherits(Login, EventEmitter);


Login.prototype.command = function(username, password) {

    username = username || this.api.globals.awxUsername;
    password = password || this.api.globals.awxPassword;

    this.api.page.login()
        .navigate()
        .waitForElementVisible('@submit', this.api.globals.longWait)
        .waitForElementNotVisible('div.spinny')
        .setValue('@username', username)
        .setValue('@password', password)
        .click('@submit')
        .waitForElementVisible('div.spinny')
        .waitForElementNotVisible('div.spinny', () => this.emit('complete'));
};

module.exports = Login;
