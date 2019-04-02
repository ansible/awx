import path from 'path';
import uuid from 'uuid';

const GCE_SERVICE_ACCOUNT_FILE = path.resolve(__dirname, 'gce.json');
const GCE_SERVICE_ACCOUNT_FILE_ALT = path.resolve(__dirname, 'gce.alt.json');
const GCE_SERVICE_ACCOUNT_FILE_INVALID = path.resolve(__dirname, 'gce.invalid.json');
const GCE_SERVICE_ACCOUNT_FILE_MISSING = path.resolve(__dirname, 'gce.missing.json');

let credentials;

module.exports = {
    before: (client, done) => {
        credentials = client.page.credentials();

        client.login();
        client.waitForAngular();

        credentials.section.navigation
            .waitForElementVisible('@credentials')
            .click('@credentials');

        credentials
            .waitForElementVisible('div.spinny')
            .waitForElementNotVisible('div.spinny');

        credentials.section.list
            .waitForElementVisible('@add')
            .click('@add');

        credentials.section.add.section.details
            .waitForElementVisible('@save')
            .setValue('@name', `credential-${uuid().substr(0, 8)}`)
            .setValue('@type', 'Google Compute Engine', done);
    },
    'expected fields are initially visible and enabled': client => {
        const { details } = credentials.section.add.section;
        const { gce } = details.section;

        details.expect.element('@name').visible;
        details.expect.element('@description').visible;
        details.expect.element('@organization').visible;
        details.expect.element('@type').visible;

        gce.expect.element('@email').visible;
        gce.expect.element('@sshKeyData').visible;
        gce.expect.element('@project').visible;
        gce.expect.element('@serviceAccountFile').visible;

        details.expect.element('@name').enabled;
        details.expect.element('@description').enabled;
        details.expect.element('@organization').enabled;
        details.expect.element('@type').enabled;

        gce.expect.element('@email').enabled;
        gce.expect.element('@sshKeyData').enabled;
        gce.expect.element('@project').enabled;
        gce.expect.element('@serviceAccountFile').enabled;

        gce.section.serviceAccountFile.expect.element('form i[class*="folder"]').visible;
        gce.section.serviceAccountFile.expect.element('form i[class*="folder"]').enabled;
        gce.section.serviceAccountFile.expect.element('form i[class*="trash"]').not.present;
    },
    'select valid credential file': client => {
        const { details } = credentials.section.add.section;
        const { gce } = details.section;

        client.pushFileToWorker(GCE_SERVICE_ACCOUNT_FILE, file => {
            gce.section.serviceAccountFile.setValue('form input[type="file"]', file);
        });

        gce.expect.element('@email').not.enabled;
        gce.expect.element('@sshKeyData').not.enabled;
        gce.expect.element('@project').not.enabled;
        gce.expect.element('@serviceAccountFile').enabled;

        gce.section.serviceAccountFile.expect.element('form i[class*="trash"]').visible;
        gce.section.serviceAccountFile.expect.element('form i[class*="trash"]').enabled;
        gce.section.serviceAccountFile.expect.element('form i[class*="folder"]').not.present;
    },
    'deselect valid credential file': client => {
        const { details } = credentials.section.add.section;
        const { gce } = details.section;

        gce.section.serviceAccountFile.click('form i[class*="trash"]');

        gce.expect.element('@email').enabled;
        gce.expect.element('@sshKeyData').enabled;
        gce.expect.element('@project').enabled;
        gce.expect.element('@serviceAccountFile').enabled;

        gce.section.serviceAccountFile.expect.element('form i[class*="folder"]').visible;
        gce.section.serviceAccountFile.expect.element('form i[class*="folder"]').enabled;
        gce.section.serviceAccountFile.expect.element('form i[class*="trash"]').not.present;

        gce.section.email.expect.element('@error').visible;
        gce.section.sshKeyData.expect.element('@error').visible;

        gce.section.project.expect.element('@error').not.present;
        gce.section.serviceAccountFile.expect.element('@error').not.present;
    },
    'select credential file with missing field': client => {
        const { details } = credentials.section.add.section;
        const { gce } = details.section;

        client.pushFileToWorker(GCE_SERVICE_ACCOUNT_FILE_MISSING, file => {
            gce.section.serviceAccountFile.setValue('form input[type="file"]', file);
        });

        gce.expect.element('@email').not.enabled;
        gce.expect.element('@sshKeyData').not.enabled;
        gce.expect.element('@project').not.enabled;
        gce.expect.element('@serviceAccountFile').enabled;

        gce.section.serviceAccountFile.expect.element('form i[class*="trash"]').visible;
        gce.section.serviceAccountFile.expect.element('form i[class*="trash"]').enabled;
        gce.section.serviceAccountFile.expect.element('form i[class*="folder"]').not.present;

        gce.section.email.expect.element('@error').visible;

        gce.section.project.expect.element('@error').not.present;
        gce.section.serviceAccountFile.expect.element('@error').not.present;
        gce.section.sshKeyData.expect.element('@error').not.present;
    },
    'deselect credential file with missing field': client => {
        const { details } = credentials.section.add.section;
        const { gce } = details.section;

        gce.section.serviceAccountFile.click('form i[class*="trash"]');

        gce.expect.element('@email').enabled;
        gce.expect.element('@sshKeyData').enabled;
        gce.expect.element('@project').enabled;
        gce.expect.element('@serviceAccountFile').enabled;

        gce.section.serviceAccountFile.expect.element('form i[class*="folder"]').visible;
        gce.section.serviceAccountFile.expect.element('form i[class*="folder"]').enabled;
        gce.section.serviceAccountFile.expect.element('form i[class*="trash"]').not.present;

        gce.section.email.expect.element('@error').visible;
        gce.section.sshKeyData.expect.element('@error').visible;

        gce.section.project.expect.element('@error').not.present;
        gce.section.serviceAccountFile.expect.element('@error').not.present;
    },
    'select invalid credential file': client => {
        const { details } = credentials.section.add.section;
        const { gce } = details.section;

        client.pushFileToWorker(GCE_SERVICE_ACCOUNT_FILE_INVALID, file => {
            gce.section.serviceAccountFile.setValue('form input[type="file"]', file);
        });

        gce.expect.element('@email').not.enabled;
        gce.expect.element('@sshKeyData').not.enabled;
        gce.expect.element('@project').not.enabled;
        gce.expect.element('@serviceAccountFile').enabled;

        gce.section.serviceAccountFile.expect.element('form i[class*="trash"]').visible;
        gce.section.serviceAccountFile.expect.element('form i[class*="trash"]').enabled;
        gce.section.serviceAccountFile.expect.element('form i[class*="folder"]').not.present;

        gce.section.email.expect.element('@error').visible;
        gce.section.serviceAccountFile.expect.element('@error').visible;
        gce.section.sshKeyData.expect.element('@error').visible;

        gce.section.project.expect.element('@error').not.present;
    },
    'deselect invalid credential file': client => {
        const { details } = credentials.section.add.section;
        const { gce } = details.section;

        gce.section.serviceAccountFile.click('form i[class*="trash"]');

        gce.expect.element('@email').enabled;
        gce.expect.element('@sshKeyData').enabled;
        gce.expect.element('@project').enabled;
        gce.expect.element('@serviceAccountFile').enabled;

        gce.section.serviceAccountFile.expect.element('form i[class*="folder"]').visible;
        gce.section.serviceAccountFile.expect.element('form i[class*="folder"]').enabled;
        gce.section.serviceAccountFile.expect.element('form i[class*="trash"]').not.present;

        gce.section.email.expect.element('@error').visible;
        gce.section.sshKeyData.expect.element('@error').visible;

        gce.section.project.expect.element('@error').not.present;
        gce.section.serviceAccountFile.expect.element('@error').not.present;
    },
    'save valid credential file': client => {
        const add = credentials.section.add.section.details;
        const edit = credentials.section.edit.section.details;

        client.pushFileToWorker(GCE_SERVICE_ACCOUNT_FILE, file => {
            add.section.gce.section.serviceAccountFile.setValue('form input[type="file"]', file);
        });

        add.section.gce.expect.element('@email').not.enabled;
        add.section.gce.expect.element('@sshKeyData').not.enabled;
        add.section.gce.expect.element('@project').not.enabled;
        add.section.gce.expect.element('@serviceAccountFile').enabled;

        add.section.gce.section.serviceAccountFile.expect.element('form i[class*="trash"]').visible;
        add.section.gce.section.serviceAccountFile.expect.element('form i[class*="trash"]').enabled;
        add.section.gce.section.serviceAccountFile.expect.element('form i[class*="folder"]').not.present;

        add.click('@save');

        credentials
            .waitForElementVisible('div.spinny')
            .waitForElementNotVisible('div.spinny');

        edit.section.gce.expect.element('@email').enabled;
        edit.section.gce.expect.element('@project').enabled;

        edit.section.gce.expect.element('@serviceAccountFile').not.enabled;
        edit.section.gce.expect.element('@sshKeyData').not.enabled;
    },
    'select and deselect credential file when replacing private key': client => {
        const taggedTextArea = '.at-InputTaggedTextarea';
        const textArea = '.at-InputTextarea';
        const replace = 'button i[class="fa fa-undo"]';
        const revert = 'button i[class="fa fa-undo fa-flip-horizontal"]';
        const { gce } = credentials.section.edit.section.details.section;

        gce.waitForElementVisible(replace);
        // eslint-disable-next-line prefer-arrow-callback
        client.execute(function clickReplace (selector) {
            document.querySelector(selector).click();
        }, [replace]);

        gce.expect.element('@email').enabled;
        gce.expect.element('@project').enabled;
        gce.expect.element(textArea).enabled;
        gce.expect.element(taggedTextArea).not.present;
        gce.expect.element('@serviceAccountFile').enabled;

        gce.section.sshKeyData.expect.element('@error').visible;

        gce.section.email.expect.element('@error').not.present;
        gce.section.project.expect.element('@error').not.present;
        gce.section.serviceAccountFile.expect.element('@error').not.present;

        client.pushFileToWorker(GCE_SERVICE_ACCOUNT_FILE_ALT, file => {
            gce.section.serviceAccountFile.setValue('form input[type="file"]', file);
        });

        gce.expect.element('@serviceAccountFile').enabled;

        gce.expect.element('@email').not.enabled;
        gce.expect.element('@sshKeyData').not.enabled;
        gce.expect.element('@project').not.enabled;

        gce.section.email.expect.element('@error').not.present;
        gce.section.project.expect.element('@error').not.present;
        gce.section.sshKeyData.expect.element('@error').not.present;
        gce.section.serviceAccountFile.expect.element('@error').not.present;

        gce.expect.element(replace).not.present;
        gce.expect.element(revert).present;
        gce.expect.element('.input-group-append button').not.enabled;
        gce.section.serviceAccountFile.click('form i[class*="trash"]');

        gce.expect.element('@email').enabled;
        gce.expect.element('@sshKeyData').enabled;
        gce.expect.element('@project').enabled;
        gce.expect.element('@serviceAccountFile').enabled;

        gce.section.sshKeyData.expect.element('@error').visible;

        gce.section.email.expect.element('@error').not.present;
        gce.section.project.expect.element('@error').not.present;
        gce.section.serviceAccountFile.expect.element('@error').not.present;

        gce.expect.element('.input-group-append button').enabled;
        // eslint-disable-next-line prefer-arrow-callback
        client.execute(function clickRevert (selector) {
            document.querySelector(selector).click();
        }, [revert]);

        gce.expect.element('@email').enabled;
        gce.expect.element('@project').enabled;

        gce.expect.element('@serviceAccountFile').not.enabled;
        gce.expect.element('@sshKeyData').not.enabled;

        client.end();
    }
};
