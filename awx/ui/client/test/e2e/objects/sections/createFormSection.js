const inputOptions = {
    inputClass: 'at-Input',
    containerClass: 'at-InputContainer',
    containerElements: {
        button: '.at-InputGroup-button',
        label: '.at-InputLabel',
        hint: '.at-InputLabel-hint',
        help: '.at-Popover-icon',
        popover: '.at-Popover-container',
        error: '.at-InputMessage--rejected',
        prompt: 'input[type="checkbox"]',
    }
};


// WIP: need to define these
const legacyInputOptions = {
    inputClass: 'form-control',
    containerClass: 'Form-formGroup',
    containerElements: {
        button: '.at-InputGroup-button',
        label: '.at-InputLabel',
        hint: '.at-InputLabel-hint',
        help: '.at-Popover-icon',
        popover: '.at-Popover-container',
        error: '.at-InputMessage--rejected',
        prompt: 'input[type="checkbox"]',
    }  
};


const generateInputSelectors = (label, options) => {
    let { containerClass, containerElements, inputClass } = options;

    // descend until span with matching text attribute is encountered
    let span = `.//span[text()="${label}"]`;
    // recurse upward until ancestor div with container class attribute is encountered
    let container = `${span}/ancestor::div[contains(@class, "${containerClass}")]`;
    // descend until element with input class attribute is encountered
    let input = `${container}//*[contains(concat(' ', @class, ' '), ' ${inputClass} ')]`;

    let inputContainer = {
        locateStrategy: 'xpath',
        selector: container,
        elements: containerElements 
    };

    let inputElement = {
        locateStrategy: 'xpath',
        selector: input
    };

    return { inputElement, inputContainer };
};


const generatorOptions = {
    default: inputOptions,
    legacy: legacyInputOptions,
};


const createFormSection = ({ selector, labels, strategy }) => {
    let options = generatorOptions[strategy || 'default'];

    let formSection = {
        selector,
        sections: {},
        elements: {}
    };

    for (let key in labels) {
        let label = labels[key];
        let { inputElement, inputContainer } = generateInputSelectors(label, options);
      
        formSection.elements[key] = inputElement;
        formSection.sections[key] = inputContainer;
    };

    return formSection;   
};

module.exports = createFormSection;
