/* Utility function to wait for the working spinner to disappear. */
exports.command = function waitForSpinny () {
    const selector = 'div.spinny';
    this
        .waitForElementVisible(selector)
        .waitForElementNotVisible(selector);
    return this;
};
