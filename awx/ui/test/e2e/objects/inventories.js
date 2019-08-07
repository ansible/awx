import actions from './sections/actions';
import breadcrumb from './sections/breadcrumb';
import createFormSection from './sections/createFormSection';
import createTableSection from './sections/createTableSection';
import header from './sections/header';
import lookupModal from './sections/lookupModal';
import navigation from './sections/navigation';
import pagination from './sections/pagination';
import permissions from './sections/permissions';
import search from './sections/search';

const standardInvDetails = createFormSection({
    selector: 'form',
    props: {
        formElementSelectors: [
            '#inventory_form .Form-textInput',
            '#inventory_form select.Form-dropDown',
            '#inventory_form .Form-textArea',
            '#inventory_form input[type="checkbox"]',
            '#inventory_form .ui-spinner-input',
            '#inventory_form .atSwitch-inner'
        ]
    },
    labels: {
        name: 'Name',
        description: 'Description',
        organization: 'Organization'
    }
});

const smartInvDetails = createFormSection({
    selector: 'form',
    props: {
        formElementSelectors: [
            '#smartinventory_form input.Form-textInput',
            '#smartinventory_form textarea.Form-textArea',
            '#smartinventory_form .Form-lookupButton',
            '#smartinventory_form #InstanceGroups'
        ]
    }
});

module.exports = {
    url () {
        return `${this.api.globals.launch_url}/#/inventories`;
    },
    sections: {
        header,
        navigation,
        breadcrumb,
        lookupModal,
        addStandardInventory: {
            selector: 'div[ui-view="form"]',
            sections: {
                standardInvDetails
            },
            elements: {
                title: 'div[class^="Form-title"]'
            }
        },
        editStandardInventory: {
            selector: 'div[ui-view="form"]',
            sections: {
                standardInvDetails,
                permissions
            },
            elements: {
                title: 'div[class^="Form-title"]'
            }
        },
        addSmartInventory: {
            selector: 'div[ui-view="form"]',
            sections: {
                smartInvDetails
            },
            elements: {
                title: 'div[class^="Form-title"]'
            }
        },
        editSmartInventory: {
            selector: 'div[ui-view="form"]',
            sections: {
                smartInvDetails,
                permissions
            },
            elements: {
                title: 'div[class^="Form-title"]'
            }
        },
        list: {
            selector: '.at-Panel',
            elements: {
                badge: 'span[class~="badge"]',
                title: 'div[class="List-titleText"]',
                add: 'button[class~="List-dropdownButton"]'
            },
            sections: {
                search,
                pagination,
                table: createTableSection({
                    elements: {
                        status: 'td[class~="status-column"]',
                        name: 'td[class~="name-column"]',
                        kind: 'td[class~="kind-column"]',
                        organization: 'td[class~="organization-column"]'
                    },
                    sections: {
                        actions
                    }
                })
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
        selectAdd (name) {
            this.api.waitForElementVisible('#button-add');
            this.expect.element('#button-add').enabled;
            this.api.click('#button-add');

            this.api.useXpath();
            this.api.waitForElementVisible(`.//a[normalize-space(text())="${name}"]`);
            this.api.click(`//a[normalize-space(text())="${name}"]`);
            this.api.useCss();

            return this;
        }
    }]
};
