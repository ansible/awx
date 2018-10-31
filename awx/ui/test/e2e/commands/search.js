exports.command = function search (selector, value, spinny = true) {
    this.waitForElementPresent(selector);
    this.waitForElementVisible(selector);
    this.clearValue(selector)
    this.setValue(selector, [value, this.Keys.ENTER])
    this.pause(1000)

    if (spinny) {
        this.pause(1000);
        this.waitForElementNotVisible('div.spinny');
    }

    return this;
};
