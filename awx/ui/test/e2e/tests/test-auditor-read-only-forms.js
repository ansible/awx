import {
    getAdminAWSCredential,
    getAdminMachineCredential,
    getAuditor,
    getInventory,
    getInventoryScript,
    getNotificationTemplate,
    getOrganization,
    getSmartInventory,
    getTeam,
    getUpdatedProject,
    getUser
} from '../fixtures';

const data = {};

let credentials;
let inventoryScripts;
let notificationTemplates;
let organizations;
let projects;
// let templates;
let users;
let inventories;
let teams;

module.exports = {
    before: (client, done) => {
        const promises = [
            getAuditor().then(obj => { data.auditor = obj; }),
            getOrganization().then(obj => { data.organization = obj; }),
            getInventory().then(obj => { data.inventory = obj; }),
            getInventoryScript().then(obj => { data.inventoryScript = obj; }),
            getAdminAWSCredential().then(obj => { data.adminAWSCredential = obj; }),
            getAdminMachineCredential().then(obj => { data.adminMachineCredential = obj; }),
            getSmartInventory().then(obj => { data.smartInventory = obj; }),
            getTeam().then(obj => { data.team = obj; }),
            getUser().then(obj => { data.user = obj; }),
            getNotificationTemplate().then(obj => { data.notificationTemplate = obj; }),
            getUpdatedProject().then(obj => { data.project = obj; })
        ];

        Promise.all(promises)
            .then(() => {
                client.useCss();

                credentials = client.page.credentials();
                inventoryScripts = client.page.inventoryScripts();
                // templates = client.page.templates();
                notificationTemplates = client.page.notificationTemplates();
                organizations = client.page.organizations();
                projects = client.page.projects();
                users = client.page.users();
                inventories = client.page.inventories();
                teams = client.page.teams();

                client.login(data.auditor.username);
                client.waitForAngular();

                done();
            });
    },
    'verify an auditor\'s credentials inputs are read-only': client => {
        const url = `${credentials.url()}/${data.adminAWSCredential.id}/`;

        client.navigateTo(url);

        credentials.section.edit
            .expect.element('@title').text.contain(data.adminAWSCredential.name);

        credentials.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify an auditor\'s inventory scripts inputs are read-only': client => {
        const url = `${inventoryScripts.url()}/${data.inventoryScript.id}/`;

        client.navigateTo(url);

        inventoryScripts.section.edit
            .expect.element('@title').text.contain(data.inventoryScript.name);

        inventoryScripts.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on inventory scripts form': () => {
        inventoryScripts.expect.element('@save').to.not.be.visible;
    },
    // TODO: re-enable these tests when JT edit has been re-factored to reliably show/remove the
    // loading spinner only one time.  Without this, we can't tell when all the requisite data is
    //  available.
    //
    // 'verify an auditor\'s job template inputs are read-only': function (client) {
    //     const url = `${templates.url()}/job_template/${data.jobTemplate.id}/`;
    //     client.navigateTo(url)''
    //
    //     templates.section.editJobTemplate
    //         .expect.element('@title').text.contain(data.jobTemplate.name);
    //
    //     templates.section.edit.section.details.checkAllFieldsDisabled();
    // },
    // 'verify save button hidden from auditor on job templates form': function () {
    //     templates.expect.element('@save').to.not.be.visible;
    // },
    'verify an auditor\'s notification templates inputs are read-only': client => {
        const url = `${notificationTemplates.url()}/${data.notificationTemplate.id}/`;

        client.navigateTo(url);

        notificationTemplates.section.edit
            .expect.element('@title').text.contain(data.notificationTemplate.name);

        notificationTemplates.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on notification templates page': () => {
        notificationTemplates.expect.element('@save').to.not.be.visible;
    },
    'verify an auditor\'s organizations inputs are read-only': client => {
        const url = `${organizations.url()}/${data.organization.id}/`;

        client.navigateTo(url);

        organizations.section.edit
            .expect.element('@title').text.contain(data.organization.name);

        organizations.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on organizations form': () => {
        organizations.expect.element('@save').to.not.be.visible;
    },
    'verify an auditor\'s smart inventory inputs are read-only': client => {
        const url = `${inventories.url()}/smart/${data.smartInventory.id}/`;

        client.navigateTo(url);

        inventories.section.editSmartInventory
            .expect.element('@title').text.contain(data.smartInventory.name);

        inventories.section.editSmartInventory.section.smartInvDetails.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on smart inventories form': () => {
        inventories.expect.element('@save').to.not.be.visible;
    },
    'verify an auditor\'s project inputs are read-only': client => {
        const url = `${projects.url()}/${data.project.id}/`;

        client.navigateTo(url);

        projects.section.edit
            .expect.element('@title').text.contain(data.project.name);

        projects.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on projects form': () => {
        projects.expect.element('@save').to.not.be.visible;
    },
    'verify an auditor\'s standard inventory inputs are read-only': client => {
        const url = `${inventories.url()}/inventory/${data.inventory.id}/`;

        client.navigateTo(url);

        inventories.section.editStandardInventory
            .expect.element('@title').text.contain(data.inventory.name);

        inventories.section.editStandardInventory.section.standardInvDetails
            .checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on standard inventory form': () => {
        inventories.expect.element('@save').to.not.be.visible;
    },
    'verify an auditor\'s teams inputs are read-only': client => {
        const url = `${teams.url()}/${data.team.id}/`;

        client.navigateTo(url);

        teams.section.edit
            .expect.element('@title').text.contain(data.team.name);

        teams.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on teams form': () => {
        teams.expect.element('@save').to.not.be.visible;
    },
    'verify an auditor\'s user inputs are read-only': client => {
        const url = `${users.url()}/${data.user.id}/`;

        client.navigateTo(url);

        users.section.edit
            .expect.element('@title').text.contain(data.user.username);

        users.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on users form': client => {
        users.expect.element('@save').to.not.be.visible;

        client.end();
    }
};
