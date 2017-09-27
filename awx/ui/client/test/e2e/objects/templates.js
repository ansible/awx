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

const details = createFormSection({
    selector: 'form',
    props: {
        formElementSelectors: [
            '#job_template_form .Form-textInput',
            '#job_template_form select.Form-dropDown',
            '#job_template_form .Form-textArea',
            '#job_template_form input[type="checkbox"]',
            '#job_template_form .ui-spinner-input',
            '#job_template_form .ScheduleToggle-switch'
        ]
    }
});

module.exports = {
    url() {
        return `${this.api.globals.launch_url}/#/templates`;
    },
    sections: {
        header,
        navigation,
        breadcrumb,
        lookupModal,
        addJobTemplate: {
            selector: 'div[ui-view="form"]',
            sections: {
                details
            },
            elements: {
                title: 'div[class^="Form-title"]'
            }
        },
        editJobTemplate: {
            selector: 'div[ui-view="form"]',
            sections: {
                details,
                permissions
            },
            elements: {
                title: 'div[class^="Form-title"]'
            }
        },
        addWorkflowJobTemplate: {
            selector: 'div[ui-view="form"]',
            sections: {
                details
            },
            elements: {
                title: 'div[class^="Form-title"]'
            }
        },
        editWorkflowJobTemplate: {
            selector: 'div[ui-view="form"]',
            sections: {
                details,
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
                add: 'button[class~="List-buttonSubmit"]'
            },
            sections: {
                search,
                pagination,
                table: createTableSection({
                    elements: {
                        name: 'td[class~="name-column"]',
                        kind: 'td[class~="type-column"]'
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
