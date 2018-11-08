const spinny = "//*[contains(@class, 'spinny')]";

exports.command = function findThenClick (selector) {
    this.waitForElementPresent(selector, () => {
        this.moveToElement(selector, 0, 0, () => {
            this.click(selector, () => {
                this.waitForElementNotVisible(spinny);
            });
        });
    });
    return this;
};
