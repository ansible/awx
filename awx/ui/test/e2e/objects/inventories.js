import actions from './sections/actions.js';
import breadcrumb from './sections/breadcrumb.js';
import createFormSection from './sections/createFormSection.js';
import createTableSection from './sections/createTableSection.js';
import header from './sections/header.js';
import lookupModal from './sections/lookupModal.js';
import navigation from './sections/navigation.js';
import pagination from './sections/pagination.js';
import permissions from './sections/permissions.js';
import search from './sections/search.js';

const standardInvDetails = createFormSection({
    selector: 'form',
    props: {
        formElementSelectors: [
            '#inventory_form .Form-textInput',
            '#inventory_form select.Form-dropDown',
            '#inventory_form .Form-textArea',
            '#inventory_form input[type="checkbox"]',
            '#inventory_form .ui-spinner-input',
            '#inventory_form .ScheduleToggle-switch'
        ]
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
    url() {
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
            selector: 'div[ui-view="list"]',
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
    }
};
