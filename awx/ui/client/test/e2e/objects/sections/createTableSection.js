import dynamicSection from './dynamicSection.js';


const header = {
    selector: 'thead',
    sections: {
        dynamicSection
    },
    commands: [{
        findColumnByText(text) {
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


const createTableSection = function({ elements, sections, commands }) {
    return {
        selector: 'table',
        sections: {
            header,
            dynamicSection
        },
        commands: [{
            findRowByText(text) {
                return this.section.dynamicSection.create({
                    elements,
                    sections,
                    commands,
                    name: `row[${text}]`,
                    locateStrategy: 'xpath',
                    selector: `.//tbody/tr/td//*[normalize-space(text())='${text}']/ancestor::tr`
                });
            },
            waitForRowCount(count) {
                let countReached = `tbody tr:nth-of-type(${count})`;
                this.waitForElementPresent(countReached);

                let countExceeded = `tbody tr:nth-of-type(${count + 1})`;
                this.waitForElementNotPresent(countExceeded);

                return this;
            }
        }]
    };
};


module.exports = createTableSection;
