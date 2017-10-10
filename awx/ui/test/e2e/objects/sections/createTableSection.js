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

const createTableSection = ({ elements, sections, commands }) => {
    const tableSection = {
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
            findRowByIndex (index) {
                return this.section.dynamicSection.create({
                    elements,
                    sections,
                    commands,
                    name: `row[${index}]`,
                    locateStrategy: 'xpath',
                    selector: `.//tbody/tr[${index}]`
                });
            },
            clickRowByIndex (index) {
                this.findRowByIndex(index).click('@self');
                return this;
            },
            waitForRowCount (count) {
                const countReached = this.findRowByIndex(count);
                countReached.waitForElementVisible('@self', 10000);

                const countExceeded = this.findRowByIndex(count + 1);
                countExceeded.waitForElementNotPresent('@self', 10000);

                return this;
            }
        }]
    };

    return tableSection;
};

module.exports = createTableSection;
