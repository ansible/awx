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
    reset: 'a[class~="reset"]',
    down: 'span[class^="fa-angle-down"]',
    up: 'span[class^="fa-angle-up"]',
    prompt: {
        locateStrategy: 'xpath',
        selector: `.//p[${normalized}='prompt on launch']/preceding-sibling::input`
    },
    show: {
        locateStrategy: 'xpath',
        selector: './/i[contains(@class, "fa fa-eye")]'
    },
    hide: {
        locateStrategy: 'xpath',
        selector: './/i[contains(@class, "fa fa-eye-slash")]'
    },
    on: {
        locateStrategy: 'xpath',
        selector: `.//button[${normalized}='on']`
    },
    off: {
        locateStrategy: 'xpath',
        selector: `.//button[${normalized}='off']`
    },
    replace: {
        locateStrategy: 'xpath',
        selector: './/i[contains(@class, "fa fa-undo")]'
    },
    revert: {
        locateStrategy: 'xpath',
        selector: './/i[contains(@class, "fa fa-undo fa-flip-horizontal")]'
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

const generateInputSelectors = (label, containerElements) => {
    // descend until span with matching text attribute is encountered
    const span = `.//span[text()="${label}"]`;
    // recurse upward until div with form-group in class attribute is encountered
    const container = `${span}/ancestor::div[contains(@class, 'form-group')]`;
    // descend until element with form-control in class attribute is encountered
    const input = `${container}//*[contains(@class, 'form-control')]`;

    const inputContainer = {
        locateStrategy: 'xpath',
        selector: container,
        elements: containerElements
    };

    const inputElement = {
        locateStrategy: 'xpath',
        selector: input
    };

    return { inputElement, inputContainer };
};

function checkAllFieldsDisabled () {
    const client = this.client.api;

    const selectors = this.props.formElementSelectors ? this.props.formElementSelectors : [
        '.at-Input'
    ];

    selectors.forEach(selector => {
        client.elements('css selector', selector, inputs => {
            inputs.value.map(o => o.ELEMENT).forEach(id => {
                if (selector.includes('atSwitch')) {
                    client.elementIdAttribute(id, 'class', ({ value }) => {
                        const isDisabled = value && value.includes('atSwitch-disabled');
                        client.assert.equal(isDisabled, true);
                    });
                } else {
                    client.elementIdAttribute(id, 'disabled', ({ value }) => {
                        client.assert.equal(value, 'true');
                    });
                }
            });
        });
    });
}

const generatorOptions = {
    default: inputContainerElements,
    legacy: legacyContainerElements
};

const createFormSection = ({ selector, labels, strategy, props }) => {
    const options = generatorOptions[strategy || 'default'];

    const formSection = {
        props,
        selector,
        sections: {},
        elements: {},
        commands: [{ checkAllFieldsDisabled }]
    };

    if (!labels) {
        return formSection;
    }

    Object.keys(labels)
        .forEach(key => {
            const label = labels[key];
            const { inputElement, inputContainer } = generateInputSelectors(label, options);

            formSection.elements[key] = inputElement;
            formSection.sections[key] = inputContainer;
        });

    return formSection;
};

module.exports = createFormSection;
