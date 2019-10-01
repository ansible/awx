import actions from './sections/actions';
import breadcrumb from './sections/breadcrumb';
import createTableSection from './sections/createTableSection';
import header from './sections/header';
import lookupModal from './sections/lookupModal';
import navigation from './sections/navigation';
import pagination from './sections/pagination';
import permissions from './sections/permissions';
import search from './sections/search';

const row = '.at-List-container .at-Row';

const addEditElements = {
    name: '#application_name_group input',
    description: '#application_description_group input',
    organization: '#application_organization_group input',
    authorizationGrantType: '#application_authorization_grant_type_group select',
    redirectUris: '#application_redirect_uris_group input',
    clientType: '#application_client_type_group select',
    save: 'button[type=save]',
    tokensTab: 'div.card button.at-Tab:nth-of-type(2)',
};

const authorizationGrantTypeOptions = {
    authorizationCode: 'Authorization code',
    resourceOwnerPasswordBased: 'Resource owner password-based',
};

const clientTypeOptions = {
    confidential: 'Confidential',
    public: 'Public',
};

module.exports = {
    url () {
        return `${this.api.globals.launch_url}/#/applications`;
    },
    commands: [{
        load () {
            this.api.url('data:,'); // https://github.com/nightwatchjs/nightwatch/issues/1724
            return this.navigate();
        },
        create (application, organization) {
            this.section.list
                .waitForElementVisible('@add')
                .click('@add');
            this.section.add
                .waitForElementVisible('@name')
                .setValue('@name', application.name)
                .setValue('@organization', organization.name)
                .setValue('@authorizationGrantType', application.authorizationGrantType)
                .setValue('@clientType', application.clientType);
            if (application.description) {
                this.section.add.setValue('@description', application.description);
            }
            if (application.redirectUris) {
                this.section.add.setValue('@redirectUris', application.redirectUris);
            }
            this.section.add.click('@save'); // flake avoidance. triple click ensures it works.
            this.section.add.click('@save');
            this.section.add.click('@save');
            this
                .waitForElementVisible('#alert-modal-msg')
                .expect.element('#alert-modal-msg').text.contain(application.name);
            this.findThenClick('#alert_ok_btn', 'css');
            this.waitForElementNotVisible('#alert-modal-msg');
        },
        delete (name) {
            this.search(name);
            const deleteButton = `${row} i[class*="fa-trash"]`;
            const modalAction = '.modal-dialog #prompt_action_btn';
            this
                .waitForElementVisible(deleteButton)
                .click(deleteButton)
                .waitForElementVisible(modalAction)
                .click(modalAction)
                .waitForSpinny();
            const searchResults = '.at-List--empty';
            this
                .waitForElementVisible(searchResults)
                .expect.element(searchResults).text.equal('PLEASE ADD ITEMS TO THIS LIST.');
        },
        search (name) {
            const searchSection = this.section.list.section.search;
            searchSection.setValue('@input', name);
            searchSection.expect.element('@searchButton').to.be.enabled.before(200);
            searchSection.click('@searchButton');
            this.waitForSpinny();
            this.waitForElementNotPresent(`${row}:nth-of-type(2)`);
            this.expect.element('.at-Panel-headingTitleBadge').text.to.equal('1');
            this.expect.element(`${row} .at-RowItem-header`).text.equal(name);
        },
    }],
    sections: {
        header,
        navigation,
        breadcrumb,
        lookupModal,
        add: {
            selector: 'div[ui-view="add"]',
            sections: {
                // details
            },
            elements: addEditElements,
        },
        edit: {
            selector: 'div[ui-view="edit"]',
            sections: {
                // details,
                permissions
            },
            elements: addEditElements,
        },
        list: {
            selector: 'div[ui-view="list"]',
            elements: {
                badge: 'span[class~="badge"]',
                title: 'h3[class~="Panel-headingTitle"]',
                add: '#button-add'
            },
            sections: {
                search,
                pagination,
                table: createTableSection({
                    elements: {
                        username: 'td[class~="username-column"]',
                        first_name: 'td[class~="first_name-column"]',
                        last_name: 'td[class~="last_name-column"]'
                    },
                    sections: {
                        actions
                    }
                })
            }
        },
        tokens: {
            selector: 'div.card',
            elements: {
                list: '.at-List-container',
            }
        }
    },
    elements: {
        cancel: 'button[class*="Form-cancelButton"]',
        save: 'button[class*="Form-saveButton"]'
    },
    props () {
        return {
            authorizationGrantTypeOptions,
            clientTypeOptions,
        };
    }
};
