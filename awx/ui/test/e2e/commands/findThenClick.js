/* Utility function for clicking elements; attempts to scroll to
 * the element if necessary, and waits for the page to finish loading.
 *
 * @param selector - xpath or css selector of the element to click.
 * @param [locatoryStrategy='xpath'] - locator strategy used. */

exports.command = function findThenClick (selector, locatorStrategy = 'xpath') {
    this.waitForElementPresent(selector, () => {
        this.moveToElement(selector, 0, 0, () => {
            this.click(selector, () => {
                if (locatorStrategy === 'css') {
                    this.waitForElementNotVisible('.spinny');
                } else {
                    this.waitForElementNotVisible('//*[contains(@class, "spinny")]');
                }
            });
        });
    });
    return this;
};
