const spinny = "//*[contains(@class, 'spinny')]";

/* Utility function for clicking elements; attempts to scroll to
 * the element if necessary, and waits for the page to finish loading.
 *
 * @param selector - xpath of the element to click. */
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
