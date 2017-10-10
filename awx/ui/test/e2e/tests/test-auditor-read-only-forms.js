import { all } from '../api.js';

import {
    getAdminAWSCredential,
    getAdminMachineCredential,
    getAuditor,
    getInventory,
    getInventoryScript,
    getNotificationTemplate,
    getOrCreate,
    getOrganization,
    getSmartInventory,
    getTeam,
    getUpdatedProject,
    getUser
} from '../fixtures.js';



let data = {};

let credentials,
    inventoryScripts,
    templates,
    notificationTemplates,
    organizations,
    projects,
    users,
    inventories,
    teams;


function navigateAndWaitForSpinner(client, url) {
    client
        .url(url)
        .waitForElementVisible('div.spinny')
        .waitForElementNotVisible('div.spinny');
}


module.exports = {
    before: function (client, done) {
        all([
            getAuditor().then(obj => data.auditor = obj),
            getOrganization().then(obj => data.organization = obj),
            getInventory().then(obj => data.inventory = obj),
            getInventoryScript().then(obj => data.inventoryScript = obj),
            getAdminAWSCredential().then(obj => data.adminAWSCredential = obj),
            getAdminMachineCredential().then(obj => data.adminMachineCredential = obj),
            getSmartInventory().then(obj => data.smartInventory = obj),
            getTeam().then(obj => data.team = obj),
            getUser().then(obj => data.user = obj),
            getNotificationTemplate().then(obj => data.notificationTemplate = obj),
            getUpdatedProject().then(obj => data.project = obj)
        ])
        .then(() => {
            client.useCss();

            credentials = client.page.credentials();
            inventoryScripts = client.page.inventoryScripts();
            templates = client.page.templates();
            notificationTemplates = client.page.notificationTemplates();
            organizations = client.page.organizations();
            projects = client.page.projects();
            users = client.page.users();
            inventories = client.page.inventories();
            teams = client.page.teams();

            client.login(data.auditor.username, data.auditor.password);
            client.waitForAngular();

            done();
        });
    },
    'verify an auditor\'s credentials inputs are read-only': function (client) {
        navigateAndWaitForSpinner(client, `${credentials.url()}/${data.adminAWSCredential.id}/`);

        credentials.section.edit
            .expect.element('@title').text.contain(data.adminAWSCredential.name);
        
        credentials.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify an auditor\'s inventory scripts inputs are read-only': function (client) {
        navigateAndWaitForSpinner(client, `${inventoryScripts.url()}/${data.inventoryScript.id}/`);

        inventoryScripts.section.edit
            .expect.element('@title').text.contain(data.inventoryScript.name);

        inventoryScripts.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on inventory scripts form': function () {
        inventoryScripts.expect.element('@save').to.not.be.visible;
    },
    // TODO: re-enable these tests when JT edit has been re-factored to reliably show/remove the loading spinner
    // only one time.  Without this, we can't tell when all the requisite data is available.
    // 'verify an auditor\'s job template inputs are read-only': function (client) {
    //     navigateAndWaitForSpinner(client, `${templates.url()}/job_template/${data.jobTemplate.id}/`);
    //
    //     templates.section.editJobTemplate
    //         .expect.element('@title').text.contain(data.jobTemplate.name);
    //
    //     templates.section.edit.section.details.checkAllFieldsDisabled();
    // },
    // 'verify save button hidden from auditor on job templates form': function () {
    //     templates.expect.element('@save').to.not.be.visible;
    // },
    'verify an auditor\'s notification templates inputs are read-only': function (client) {
        navigateAndWaitForSpinner(client, `${notificationTemplates.url()}/${data.notificationTemplate.id}/`);

        notificationTemplates.section.edit
            .expect.element('@title').text.contain(data.notificationTemplate.name);

        notificationTemplates.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on notification templates page': function () {
        notificationTemplates.expect.element('@save').to.not.be.visible;
    },
    'verify an auditor\'s organizations inputs are read-only': function (client) {
        navigateAndWaitForSpinner(client, `${organizations.url()}/${data.organization.id}/`);

        organizations.section.edit
            .expect.element('@title').text.contain(data.organization.name);

        organizations.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on organizations form': function () {
        organizations.expect.element('@save').to.not.be.visible;
    },
    'verify an auditor\'s smart inventory inputs are read-only': function (client) {
        navigateAndWaitForSpinner(client, `${inventories.url()}/smart/${data.smartInventory.id}/`);

        inventories.section.editSmartInventory
            .expect.element('@title').text.contain(data.smartInventory.name);

        inventories.section.editSmartInventory.section.smartInvDetails.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on smart inventories form': function () {
        inventories.expect.element('@save').to.not.be.visible;
    },
    'verify an auditor\'s project inputs are read-only': function (client) {
        navigateAndWaitForSpinner(client, `${projects.url()}/${data.project.id}/`);

        projects.section.edit
            .expect.element('@title').text.contain(data.project.name);

        projects.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on projects form': function () {
        projects.expect.element('@save').to.not.be.visible;
    },
    'verify an auditor\'s standard inventory inputs are read-only': function (client) {
        navigateAndWaitForSpinner(client, `${inventories.url()}/inventory/${data.inventory.id}/`);

        inventories.section.editStandardInventory
            .expect.element('@title').text.contain(data.inventory.name);

        inventories.section.editStandardInventory.section.standardInvDetails.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on standard inventory form': function () {
        inventories.expect.element('@save').to.not.be.visible;
    },
    'verify an auditor\'s teams inputs are read-only': function (client) {
        navigateAndWaitForSpinner(client, `${teams.url()}/${data.team.id}/`);

        teams.section.edit
            .expect.element('@title').text.contain(data.team.name);

        teams.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on teams form': function () {
        teams.expect.element('@save').to.not.be.visible;
    },
    'verify an auditor\'s user inputs are read-only': function (client) {
        navigateAndWaitForSpinner(client, `${users.url()}/${data.user.id}/`);

        users.section.edit
            .expect.element('@title').text.contain(data.user.username);

        users.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on users form': function (client) {
        users.expect.element('@save').to.not.be.visible;

        client.end();
    }
};
