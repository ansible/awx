module.exports = {
    url() {
	return `${this.api.globals.launch_url}/#/login`
    },
    elements: {
        username: '#login-username',
        password: '#login-password',
        submit: '#login-button',
        logo: '#main_menu_logo'
    }
};
