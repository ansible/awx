exports.command = function navigateTo (url) {
    this.url(url);

    this.waitForElementVisible('div.spinny');
    this.waitForElementNotVisible('div.spinny');

    return this;
};
