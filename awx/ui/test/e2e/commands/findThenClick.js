exports.command = function findThenClick (selector) {
    this.waitForElementPresent(selector, function() {
        this.moveToElement(selector, 0, 0, function() {
            this.click(selector);
        });
    });
    return this;
};
