/* Utility function to wait for the working spinner to disappear. */
exports.command = function waitForSpinny (useXpath = false) {
    let selector = 'div.spinny';
    if (useXpath) {
        selector = '//*[contains(@class, "spinny")]';
    }
    this.waitForElementVisible(selector);
    // if a process is running for an extended period,
    // spinny might last longer than five seconds.
    // this gives it a max of 30 secs before failing.
    this.waitForElementNotVisible(selector, 30000);
    return this;
};
