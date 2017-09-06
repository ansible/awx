import _ from 'lodash';

import breadcrumb from './sections/breadcrumb.js';
import createFormSection from './sections/createFormSection.js';
import createTableSection from './sections/createTableSection.js';
import dynamicSection from './sections/dynamicSection.js';
import header from './sections/header.js';
import permissions from './sections/permissions.js';
import search from './sections/search.js';


const common = createFormSection({
    selector: '.at-Panel-body form',
    labels: {
        name: "Name",
        description: "Description",
        organization: "Organization",
        type: "Credential type"
    }
});


const machine = createFormSection({
    selector: '.at-InputGroup-inset',
    labels: {
        username: "Username",
        password: "Password",
        sshKeyData: "SSH Private Key",
        sshKeyUnlock: "Private Key Passphrase",
        becomeMethod: "Privilege Escalation Method",
        becomeUsername: "Privilege Escalation Username",
        becomePassword: "Privilege Escalation Password"
    }
});


const vault = createFormSection({
    selector: '.at-InputGroup-inset',
    labels: {
        vaultPassword: "Vault Password",
    }
});


const scm = createFormSection({
    selector: '.at-InputGroup-inset',
    labels: {
        username: "Username",
        password: "Password",
        sshKeyData: "SCM Private Key",
        sshKeyUnlock: "Private Key Passphrase",
    }
});


const aws = createFormSection({
    selector: '.at-InputGroup-inset',
    labels: {
        accessKey: "Access Key",
        secretKey: "Secret Key",
        securityToken: "STS Token",
    }
});


const gce = createFormSection({
    selector: '.at-InputGroup-inset',
    labels: {
        email: "Service Account Email Address",
        project: "Project",
        sshKeyData: "RSA Private Key",
    }
});


const vmware = createFormSection({
    selector: '.at-InputGroup-inset',
    labels: {
        host: "VCenter Host",
        username: "Username",
        password: "Password",
    }
});


const azureClassic = createFormSection({
    selector: '.at-InputGroup-inset',
    labels: {
        subscription: "Subscription ID",
        sshKeyData: "Management Certificate",
    }
});


const azure = createFormSection({
    selector: '.at-InputGroup-inset',
    labels: {
        subscription: "Subscription ID",
        username: "Username",
        password: "Password",
        client: "Client ID",
        secret: "Client Secret",
        tenant: "Tenant ID",
    }
});


const openStack = createFormSection({
    selector: '.at-InputGroup-inset',
    labels: {
        username: "Username",
        password: "Password (API Key)",
        host: "Host (Authentication URL)",
        project: "Project (Tenant Name)",
        domain: "Domain Name",
    }
});


const rackspace = createFormSection({
    selector: '.at-InputGroup-inset',
    labels: {
        username: "Username",
        password: "Password",
    }
});


const cloudForms = createFormSection({
    selector: '.at-InputGroup-inset',
    labels: {
        host: "Cloudforms URL",
        username: "Username",
        password: "Password",
    }
});


const network = createFormSection({
    selector: '.at-InputGroup-inset',
    labels: {
        sshKeyData: "SSH Private Key",
        sshKeyUnlock: "Private Key Passphrase",
        username: "Username",
        password: "Password",
        authorizePassword: "Authorize Password",
    }
});

network.elements.authorize = {
    locateStrategy: 'xpath',
    selector: '//input[../p/text() = "Authorize"]'
};


const sat6 = createFormSection({
    selector: '.at-InputGroup-inset',
    labels: {
        host: "Satellite 6 URL",
        username: "Username",
        password: "Password",
    }
});


const insights = createFormSection({
    selector: '.at-InputGroup-inset',
    labels: {
        username: "Username",
        password: "Password",
    },
});


const details = _.merge({}, common, {
    elements: {
        cancel: '.btn[type="cancel"]',
        save: '.btn[type="save"]'
    },
    sections: {
        aws,
        azure,
        azureClassic,
        cloudForms,
        dynamicSection,
        gce,
        insights,
        machine,
        network,
        rackspace,
        sat6,
        scm,
        openStack,
        vault,
        vmware
    },
    commands: [{
        custom({ name, inputs }) {
            let labels = {};
            inputs.fields.map(f => labels[f.id] = f.label);

            let selector = '.at-InputGroup-inset';
            let generated = createFormSection({ selector, labels });

            let params = _.merge({ name }, generated);
            return this.section.dynamicSection.create(params);
        },
        clear() {
            this.clearValue('@name');
            this.clearValue('@organization');
            this.clearValue('@description');
            this.clearValue('@type');
            this.waitForElementNotVisible('.at-InputGroup-inset');
            return this;
        },
        clearAndSelectType(type) {
            this.clear();
            this.setValue('@type', type);
            this.waitForElementVisible('.at-InputGroup-inset');
            return this;
        }
    }]
});


module.exports = {
    url() {
        return `${this.api.globals.awxURL}/#/credentials`
    },
    sections: {
        header,
        breadcrumb,
        add: {
            selector: 'div[ui-view="add"]',
            elements: {
                title: '.at-Panel-headingTitle'
            },
            sections: {
                details
            }
        },
        edit: {
            selector: 'div[ui-view="edit"]',
            elements: {
                title: '.at-Panel-headingTitle'
            },
            sections: {
                details,
                permissions
            }
        },
        list: {
            selector: 'div[ui-view="list"]',
            elements: {
                add: '.List-buttonSubmit',
                badge: 'div[class="List-titleBadge]',
                titleText: 'div[class="List-titleText"]',
                noitems: 'div[class="List-noItems"]'
            },
            sections: {
                search,
                table: createTableSection({
                    selector: '#credentials_table',
                    rowElements: {
                        name: 'td[class~="name-column"]',
                    },
                })
            }
        }
    }
};
