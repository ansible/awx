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
    },
    selectSubcategory (name) {
        const spinny = 'div.spinny';
        const categoryName = `//*[text() = '${name}']`;

        this.api.useXpath();
        this.api.waitForElementVisible(categoryName);
        this.api.click(categoryName);
        this.api.useCss();

        return this;
    },
    selectDropDownContainer (name) {
        const spinny = 'div.spinny';
        const select = '#configure-dropdown-nav';
        const arrow = `${select} + span span[class$="arrow"]`;
        const option = `//li[contains(text(), "${name}")]`;

        this.api.waitForElementVisible(arrow);
        this.api.click(arrow);

        this.api.useXpath();
        this.api.waitForElementVisible(option);
        this.api.click(option);
        this.api.useCss();

        return this;
    },
}];

module.exports = {
    url () {
        return `${this.api.globals.launch_url}/#/configuration`;
    },
    sections,
    commands,
};
