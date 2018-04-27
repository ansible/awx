import breadcrumb from './sections/breadcrumb';
import header from './sections/header';
import navigation from './sections/navigation';

const sections = {
    header,
    navigation,
    breadcrumb,
};

const commands = [{
    load () {
        this.api.url('data:,'); // https://github.com/nightwatchjs/nightwatch/issues/1724
        return this.navigate();
    }
}];

module.exports = {
    url () {
        return `${this.api.globals.launch_url}/#/home`;
    },
    sections,
    commands,
};
