module.exports = {
    url() {
        return `${this.api.globals.awxURL}/#/activity_stream`
    },
    elements: {
        title: '.List-titleText',
        subtitle: '.List-titleLockup',
        category: '#stream-dropdown-nav'
    }
};
