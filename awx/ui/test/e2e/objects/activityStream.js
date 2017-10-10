module.exports = {
    url() {
        return `${this.api.globals.launch_url}/#/activity_stream`
    },
    elements: {
        title: '.List-titleText',
        subtitle: '.List-titleLockup',
        category: '#stream-dropdown-nav'
    }
};
