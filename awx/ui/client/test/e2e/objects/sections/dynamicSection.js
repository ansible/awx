const dynamicSection = {
    selector: '.',
    commands: [{
        create({ name, locateStrategy, selector, elements, sections, commands }) {
            let Section = this.constructor;

            let options = Object.assign(Object.create(this), {
                name,
                locateStrategy,
                elements,
                selector,
                sections,
                commands
            });

            options.elements.self = {
                locateStrategy: 'xpath',
                selector: '.'
            };

            return new Section(options);
        }
    }]
};

module.exports = dynamicSection;
