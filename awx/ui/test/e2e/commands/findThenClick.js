exports.command = function findThenClick (selector) {
    this
        .waitForElementPresent(selector)
        .moveToElement(selector, 0, 0)
        .click(selector);
    return this;
};
