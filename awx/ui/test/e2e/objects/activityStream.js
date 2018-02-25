module.exports = {
    url () {
        return `${this.api.globals.launch_url}/#/activity_stream`;
    },
    commands: [{
        load () {
            this.api.url('data:,'); // https://github.com/nightwatchjs/nightwatch/issues/1724
            return this.navigate();
        },
    }],
    elements: {
        title: '.List-titleText',
        subtitle: '.List-titleLockup',
        category: '#stream-dropdown-nav'
    }
};
