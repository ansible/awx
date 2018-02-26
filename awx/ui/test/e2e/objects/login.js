module.exports = {
    url () {
        return `${this.api.globals.launch_url}/#/login`;
    },
    commands: [{
        load () {
            this.api.url('data:,'); // https://github.com/nightwatchjs/nightwatch/issues/1724
            return this.navigate();
        },
    }],
    elements: {
        username: '#login-username',
        password: '#login-password',
        submit: '#login-button',
        logo: '#main_menu_logo'
    }
};
