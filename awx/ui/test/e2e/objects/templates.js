import _ from 'lodash';

import breadcrumb from './sections/breadcrumb';
import createFormSection from './sections/createFormSection';
import header from './sections/header';
import lookupModal from './sections/lookupModal';
import navigation from './sections/navigation';
import pagination from './sections/pagination';
import permissions from './sections/permissions';
import search from './sections/search';

const jtDetails = createFormSection({
    selector: 'form',
    props: {
        formElementSelectors: [
            '#job_template_form .Form-textInput',
            '#job_template_form select.Form-dropDown',
            '#job_template_form .Form-textArea',
            '#job_template_form input[type="checkbox"]',
            '#job_template_form .ui-spinner-input',
            '#job_template_form .atSwitch-inner'
        ]
    },
    labels: {
        name: 'Name',
        description: 'Description',
        playbook: 'Playbook'

    }
});

const wfjtDetails = createFormSection({
    selector: 'form',
    props: {
        formElementSelectors: [
            '#workflow_job_template_form .Form-textInput',
            '#workflow_job_template_form select.Form-dropDown',
            '#workflow_job_template_form .Form-textArea',
            '#workflow_job_template_form input[type="checkbox"]',
            '#workflow_job_template_form .ui-spinner-input',
            '#workflow_job_template_form .atSwitch-inner'
        ]
    },
    labels: {
        name: 'Name',
        description: 'Description'

    }
});

const lookupInventory = _.merge({}, lookupModal, {
    locateStrategy: 'xpath',
    selector: './/div[text()="Select inventory"]/ancestor::div[contains(@class, "modal-content")]'
});

const lookupProject = _.merge({}, lookupModal, {
    locateStrategy: 'xpath',
    selector: './/div[text()="Select project"]/ancestor::div[contains(@class, "modal-content")]'
});

module.exports = {
    url () {
        return `${this.api.globals.launch_url}/#/templates`;
    },
    sections: {
        header,
        navigation,
        breadcrumb,
        lookupInventory,
        lookupProject,
        addJobTemplate: {
            selector: 'div[ui-view="form"]',
            sections: {
                jtDetails
            },
            elements: {
                title: 'div[class^="Form-title"]'
            }
        },
        editJobTemplate: {
            selector: 'div[ui-view="form"]',
            sections: {
                jtDetails,
                permissions
            },
            elements: {
                title: 'div[class^="Form-title"]'
            }
        },
        addWorkflowJobTemplate: {
            selector: 'div[ui-view="form"]',
            sections: {
                wfjtDetails
            },
            elements: {
                title: 'div[class^="Form-title"]',
                visualizerButton: '#workflow_job_template_workflow_visualizer_btn',
            }
        },
        editWorkflowJobTemplate: {
            selector: 'div[ui-view="form"]',
            sections: {
                wfjtDetails,
                permissions
            },
            elements: {
                title: 'div[class^="Form-title"]',
                visualizerButton: '#workflow_job_template_workflow_visualizer_btn',
            }
        },
        list: {
            selector: '.at-Panel',
            elements: {
                badge: 'span[class~="badge"]',
                title: 'div[class="List-titleText"]',
                add: '#button-add'
            },
            sections: {
                search,
                pagination
            }
        }
    },
    elements: {
        cancel: 'button[class*="Form-cancelButton"]',
        save: 'button[class*="Form-saveButton"]'
    },
    commands: [{
        load () {
            this.api.url('data:,'); // https://github.com/nightwatchjs/nightwatch/issues/1724
            return this.navigate();
        },
        clickWhenEnabled (selector) {
            this.api.waitForElementVisible(selector);
            this.expect.element(selector).enabled;
            this.click(selector);
            return this;
        },
        selectAdd (name) {
            this.clickWhenEnabled('#button-add');

            this.api
                .useXpath()
                .waitForElementVisible(`.//a[normalize-space(text())="${name}"]`)
                .click(`//a[normalize-space(text())="${name}"]`)
                .useCss();

            return this;
        },
        selectPlaybook (name) {
            this.clickWhenEnabled('label[for="playbook"] + div span[class$="arrow"]');

            this.api
                .useXpath()
                .waitForElementVisible(`//li[contains(text(), "${name}")]`)
                .click(`//li[contains(text(), "${name}")]`)
                .useCss();

            return this;
        },
        selectInventory (name) {
            this.clickWhenEnabled('label[for="inventory"] + div i[class$="search"]');

            this.api
                .waitForElementVisible('div.spinny')
                .waitForElementNotVisible('div.spinny');

            this.section.lookupInventory.section.search
                .waitForElementVisible('@input')
                .waitForElementVisible('@searchButton')
                .sendKeys('@input', name)
                .click('@searchButton')
                .waitForElementVisible('div.spinny')
                .waitForElementNotVisible('div.spinny');

            this.api
                .waitForElementNotPresent('#inventories_table .List-tableRow:nth-child(2)')
                .waitForElementVisible('#inventories_table .List-tableRow:nth-child(1) input[type="radio"]')
                .click('#inventories_table .List-tableRow:nth-child(1) input[type="radio"]');

            this.section.lookupInventory.expect.element('@save').enabled;

            this.section.lookupInventory
                .click('@save');

            return this;
        },
        selectProject (name) {
            this.clickWhenEnabled('label[for="project"] + div i[class$="search"]');

            this.api
                .waitForElementVisible('div.spinny')
                .waitForElementNotVisible('div.spinny');

            this.section.lookupProject.section.search
                .waitForElementVisible('@input')
                .waitForElementVisible('@searchButton')
                .sendKeys('@input', name)
                .click('@searchButton')
                .waitForElementVisible('div.spinny')
                .waitForElementNotVisible('div.spinny');

            this.api
                .waitForElementNotPresent('#projects_table .List-tableRow:nth-child(2)')
                .waitForElementVisible('#projects_table .List-tableRow:nth-child(1) input[type="radio"]')
                .click('#projects_table .List-tableRow:nth-child(1) input[type="radio"]');

            this.section.lookupProject.expect.element('@save').enabled;

            this.section.lookupProject
                .click('@save')
                .waitForElementVisible('div.spinny')
                .waitForElementNotVisible('div.spinny');

            return this;
        },
        selectVaultCredential (name) {
            this.clickWhenEnabled('label[for="credential"] + div i[class$="search"]');

            this.api
                .waitForElementVisible('div.spinny')
                .waitForElementNotVisible('div.spinny')
                .waitForElementVisible('#multi-credential-kind-select + span span[class$="arrow"]')
                .click('#multi-credential-kind-select + span span[class$="arrow"]')
                .useXpath()
                .waitForElementVisible('//li[contains(text(), "Vault")]')
                .click('//li[contains(text(), "Vault")]')
                .useCss()
                .waitForElementVisible('div.spinny')
                .waitForElementNotVisible('div.spinny')
                .waitForElementVisible('multi-credential-modal smart-search input')
                .waitForElementVisible('multi-credential-modal smart-search i[class$="search"]')
                .sendKeys('multi-credential-modal smart-search input', name)
                .click('multi-credential-modal smart-search i[class$="search"]')
                .waitForElementVisible('div.spinny')
                .waitForElementNotVisible('div.spinny')
                .click('multi-credential-modal smart-search a[class*="clear"]')
                .waitForElementVisible('div.spinny')
                .waitForElementNotVisible('div.spinny')
                .sendKeys('multi-credential-modal smart-search input', name)
                .click('multi-credential-modal smart-search i[class$="search"]')
                .waitForElementVisible('div.spinny')
                .waitForElementNotVisible('div.spinny')
                .waitForElementNotPresent('multi-credential-modal .List-tableRow:nth-child(2)')
                .waitForElementVisible('multi-credential-modal .List-tableRow:nth-child(1) input[type="checkbox"]')
                .click('multi-credential-modal .List-tableRow:nth-child(1) input[type="checkbox"]')
                .click('multi-credential-modal button[class*="save"]')
                .pause(1000);

            return this;
        },
        selectMachineCredential (name) {
            this.clickWhenEnabled('label[for="credential"] + div i[class$="search"]');

            this.api
                .waitForElementVisible('div.spinny')
                .waitForElementNotVisible('div.spinny')
                .waitForElementVisible('#multi-credential-kind-select + span span[class$="arrow"]')
                .click('#multi-credential-kind-select + span span[class$="arrow"]')
                .useXpath()
                .waitForElementVisible('//li[contains(text(), "Machine")]')
                .click('//li[contains(text(), "Machine")]')
                .useCss()
                .waitForElementVisible('multi-credential-modal smart-search input')
                .waitForElementVisible('multi-credential-modal smart-search i[class$="search"]')
                .sendKeys('multi-credential-modal smart-search input', name)
                .click('multi-credential-modal smart-search i[class$="search"]')
                .waitForElementVisible('div.spinny')
                .waitForElementNotVisible('div.spinny')
                .waitForElementNotPresent('multi-credential-modal .List-tableRow:nth-child(2)')
                .waitForElementVisible('multi-credential-modal .List-tableRow:nth-child(1) input[type="radio"]')
                .click('multi-credential-modal .List-tableRow:nth-child(1) input[type="radio"]')
                .click('multi-credential-modal button[class*="save"]')
                .pause(1000);

            return this;
        }
    }]
};
