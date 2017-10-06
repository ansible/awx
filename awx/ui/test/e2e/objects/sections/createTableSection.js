import dynamicSection from './dynamicSection';

const header = {
    selector: 'thead',
    sections: {
        dynamicSection
    },
    commands: [{
        findColumnByText (text) {
            return this.section.dynamicSection.create({
                name: `column[${text}]`,
                locateStrategy: 'xpath',
                selector: `.//*[normalize-space(text())='${text}']/ancestor-or-self::th`,
                elements: {
                    sortable: {
                        locateStrategy: 'xpath',
                        selector: './/*[contains(@class, "fa-sort")]'
                    },
                    sorted: {
                        locateStrategy: 'xpath',
                        selector: './/*[contains(@class, "fa-sort-")]'
                    },
                }
            });
        }
    }]
};

module.exports = ({ elements, sections, commands }) => ({
    selector: 'table',
    sections: {
        header,
        dynamicSection
    },
    commands: [{
        findRowByText (text) {
            return this.section.dynamicSection.create({
                elements,
                sections,
                commands,
                name: `row[${text}]`,
                locateStrategy: 'xpath',
                selector: `.//tbody/tr/td//*[normalize-space(text())='${text}']/ancestor::tr`
            });
        },
        waitForRowCount (count) {
            const countReached = `tbody tr:nth-of-type(${count})`;
            this.waitForElementPresent(countReached);

            const countExceeded = `tbody tr:nth-of-type(${count + 1})`;
            this.waitForElementNotPresent(countExceeded);

            return this;
        }
    }]
});

