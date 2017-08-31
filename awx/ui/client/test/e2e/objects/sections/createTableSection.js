import dynamicSection from './dynamicSection.js';


const header = {
    selector: 'thead',
    sections: { dynamicSection },
    commands: [{
        column(text) {
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


module.exports = ({ selector, rowElements, rowSections, rowCommands }) => {
    return {
        selector,
        props: {
            rowElements,
            rowSections,
            rowCommands
        },
        elements: {
            self: { locateStrategy: 'xpath', selector: '.' }
        },
        sections: {
            header,
            dynamicSection
        },
        commands: [{
            row(text) {
                let self = this;
                return this.section.dynamicSection.create({
                    name: `row[${text}]`,
                    locateStrategy: 'xpath',
                    selector: `.//tbody/tr/td//*[normalize-space(text())='${text}']/ancestor::tr`,
                    elements: self.props.rowElements,
                    sections: self.props.rowSections,
                    commands: self.props.rowCommands
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
