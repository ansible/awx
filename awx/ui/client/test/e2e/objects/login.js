module.exports = {
    url() {
    	return `${this.api.globals.awxURL}/#/login`
    },
    elements: {
        username: '#login-username',
        password: '#login-password',
        submit: '#login-button',
        logo: '#main_menu_logo'
    }
};
