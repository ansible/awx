const dynamicSection = {
    selector: '.',
    commands: [{
        create(dynamicOpts) {
            let Section = this.constructor;
            let options = Object.create(this);

            options.name = `${dynamicOpts.name}(dynamic)`;
            options.locateStrategy = dynamicOpts.locateStrategy;
            options.selector = dynamicOpts.selector;
            
            options.sections = dynamicOpts.sections;
            options.commands = dynamicOpts.commands;
            options.elements = dynamicOpts.elements;
            options.elements.self = { locateStrategy: 'xpath', selector: '.' };

            return new Section(options);
        }
    }]
};

module.exports = dynamicSection;
