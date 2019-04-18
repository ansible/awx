/* Utility function to wait for the working spinner to disappear. */
exports.command = function waitForSpinny (useXpath = false) {
    let selector = 'div.spinny';
    if (useXpath) {
        selector = '//*[contains(@class, "spinny")]';
    }
    this.waitForElementVisible(selector);
    this.waitForElementNotVisible(selector);
    return this;
};
