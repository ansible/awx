module.exports = {
    url () {
        return `${this.api.globals.launch_url}/#/portal/myjobs`;
    },
    sections: {},
    elements: {},
    commands: [{
        load () {
            this.api.url('data:,'); // https://github.com/nightwatchjs/nightwatch/issues/1724
            return this.navigate();
        },
    }],
};
