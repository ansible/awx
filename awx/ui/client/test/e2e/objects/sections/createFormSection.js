import { merge } from 'lodash';


const translated = "translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')";
const normalized = `normalize-space(${translated})`;


const inputContainerElements = {
    lookup: 'button > i[class="fa fa-search"]',
    error: '.at-InputMessage--rejected',
    help: 'i[class$="fa-question-circle"]',
    hint: '.at-InputLabel-hint',
    label: 'label',
    popover: '.at-Popover-container',
    yaml: 'input[type="radio", value="yaml"]',
    json: 'input[type="radio", value="json"]',
    revert: 'a[class~="reset"]',
    down: 'span[class^="fa-angle-down"]',
    up: 'span[class^="fa-angle-up"]',
    prompt: {
        locateStrategy: 'xpath',
        selector: `.//p[${normalized}='prompt on launch']/preceding-sibling::input`
    },
    show: {
        locateStrategy: 'xpath',
        selector: `.//button[${normalized}='show']`
    },
    hide: {
        locateStrategy: 'xpath',
        selector: `.//button[${normalized}='hide']`
    },
    on: {
        locateStrategy: 'xpath',
        selector: `.//button[${normalized}='on']`
    },
    off: {
        locateStrategy: 'xpath',
        selector: `.//button[${normalized}='off']`
    }
};


const legacyContainerElements = merge({}, inputContainerElements, {
    prompt: {
        locateStrategy: 'xpath',
        selector: `.//label[${normalized}='prompt on launch']/input`
    },
    error: 'div[class~="error"]',
    popover: ':root div[id^="popover"]',
});


const generateInputSelectors = function(label, containerElements) {
    // descend until span with matching text attribute is encountered
    let span = `.//span[text()="${label}"]`;
    // recurse upward until div with form-group in class attribute is encountered
    let container = `${span}/ancestor::div[contains(@class, 'form-group')]`;
    // descend until element with form-control in class attribute is encountered
    let input = `${container}//*[contains(@class, 'form-control')]`;

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


const checkAllFieldsDisabled = function() {
    let client = this.client.api;

    let selectors = this.props.formElementSelectors ? this.props.formElementSelectors : [
        '.at-Input'
    ];

    selectors.forEach(function(selector) {
        client.elements('css selector', selector, inputs => {
            inputs.value.map(o => o.ELEMENT).forEach(id => {
                client.elementIdAttribute(id, 'disabled', ({ value }) => {
                    client.assert.equal(value, 'true');
                });
            });
        });
    });
};


const generatorOptions = {
    default: inputContainerElements,
    legacy: legacyContainerElements
};


const createFormSection = function({ selector, labels, strategy, props }) {
    let options = generatorOptions[strategy || 'default'];

    let formSection = {
        selector,
        sections: {},
        elements: {},
        commands: [{
            checkAllFieldsDisabled: checkAllFieldsDisabled
        }],
        props: props
    };

    for (let key in labels) {
        let label = labels[key];

        let { inputElement, inputContainer } = generateInputSelectors(label, options);

        formSection.elements[key] = inputElement;
        formSection.sections[key] = inputContainer;
    }

    return formSection;
};

module.exports = createFormSection;
