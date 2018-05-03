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

const details = createFormSection({
    selector: 'form',
    props: {
        formElementSelectors: [
            '#inventory_script_form .Form-textInput',
            '#inventory_script_form .Form-textArea',
            '#inventory_script_form .Form-lookupButton'
        ]
    }
});

module.exports = {
    url () {
        return `${this.api.globals.launch_url}/#/inventory_scripts`;
    },
    commands: [{
        load () {
            this.api.url('data:,'); // https://github.com/nightwatchjs/nightwatch/issues/1724
            return this.navigate();
        },
    }],
    sections: {
        header,
        navigation,
        breadcrumb,
        lookupModal,
        add: {
            selector: 'div[ui-view="form"]',
            sections: {
                details
            },
            elements: {
                title: 'div[class^="Form-title"]'
            }
        },
        edit: {
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
                add: '#button-add'
            },
            sections: {
                search,
                pagination,
                table: createTableSection({
                    elements: {
                        name: 'td[class~="name-column"]',
                        organization: 'td[class~="organization-column"]',
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
