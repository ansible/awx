import _ from 'lodash';

module.exports = {
    url () {
        return `${this.api.globals.launch_url}/#/jobs`;
    },
    sections: {}, // TODO: Fill this out
    elements: {}, // TODO: Fill this out
    commands: [{
        load () {
            this.api.url('data:,'); // https://github.com/nightwatchjs/nightwatch/issues/1724
            return this.navigate();
        },
    }],
};
