import uuid from 'uuid';


let testID = uuid().substr(0,8);


let store = {
    auditor: {
        username: `auditor-${testID}`,
        first_name: 'auditor',
        last_name: 'last',
        email: 'null@ansible.com',
        is_superuser: false,
        is_system_auditor: true,
        password: 'password'
    },
    adminJobTemplate: {
        name: `adminJobTemplate-${testID}`,
        description: `adminJobTemplate-description-${testID}`,
        project: 103,
        playbook: 'check.yml'
    },
    adminAWSCredential: {
        name: `adminAWSCredential-${testID}`,
        description: `adminAWSCredential-description-${testID}`,
        inputs: {
            username: 'username',
            password: 'password',
            security_token: 'AAAAAAAAAAAAAAAAAAAAAAAAAA'
        }
    },
    adminMachineCredential: {
        name: `adminMachineCredential-${testID}`
    },
    adminOrganization: {
        name: `adminOrganization-${testID}`,
    },
    adminInventoryScript: {
        name: `adminInventoryScript-${testID}`,
        script: '#!/usr/bin/env python'
    },
    adminNotificationTemplate: {
        name: `adminNotificationTemplate-${testID}`,
        notification_configuration: {channels: ["awx-e2e"], token: "foobar"},
        notification_type: "slack"
    },
    adminProject: {
        name: `adminProject-${testID}`,
        scm_type: "git",
        scm_url: "https://github.com/ansible/tower-example.git"
    },
    adminSmartInventory: {
        name: `adminSmartInventory-${testID}`,
        host_filter: 'search=localhost',
        kind: 'smart'
    },
    adminStandardInventory: {
        name: `adminStandardInventory-${testID}`
    },
    adminTeam: {
        name: `adminTeam-${testID}`
    },
    adminUser: {
        username: `adminUser-${testID}`,
        first_name: `adminUser-${testID}-first`,
        last_name: `adminUser-${testID}-last`,
        email: `null-${testID}@ansible.com`,
        is_superuser: false,
        is_system_auditor: false,
        password: 'password'
    },
    created: {}
};

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

        client.login();
        client.waitForAngular();

        client.inject([store, '$http'], (store, $http) => {

            let { adminJobTemplate,
                  adminAWSCredential,
                  adminMachineCredential,
                  adminOrganization,
                  adminInventoryScript,
                  adminNotificationTemplate,
                  adminProject,
                  adminSmartInventory,
                  adminStandardInventory,
                  adminTeam,
                  adminUser,
                  auditor } = store;

            return $http.get('/api/v2/me')
                .then(({ data }) => {
                    let resource = 'Amazon%20Web%20Services+cloud';
                    adminAWSCredential.user = data.results[0].id;

                    return $http.get(`/api/v2/credential_types/${resource}`);
                })
                .then(({ data }) => {
                    adminAWSCredential.credential_type = data.id;

                    return $http.post('/api/v2/credentials/', adminAWSCredential);
                })
                .then(({ data }) => {
                    adminAWSCredential = data;

                    return $http.post('/api/v2/organizations/', adminOrganization);
                })
                .then(({ data }) => {
                    adminOrganization = data;
                    adminInventoryScript.organization = data.id;
                    adminNotificationTemplate.organization = data.id;
                    adminProject.organization = data.id;
                    adminSmartInventory.organization = data.id;
                    adminStandardInventory.organization = data.id;
                    adminTeam.organization = data.id;
                    adminUser.organization = data.id;
                    adminMachineCredential.organization = data.id;

                    return $http.post('/api/v2/teams/', adminTeam);
                })
                .then(({ data }) => {
                    adminTeam = data;

                    return $http.get('/api/v2/credential_types/Machine+ssh');
                })
                .then(({ data }) => {
                    adminMachineCredential.credential_type = data.id;

                    return $http.post('/api/v2/credentials/', adminMachineCredential);
                })
                .then(({ data }) => {
                    adminMachineCredential = data;
                    adminJobTemplate.credential = data.id;

                    return $http.post('/api/v2/users/', adminUser);
                })
                .then(({ data }) => {
                    adminUser = data;

                    return $http.post('/api/v2/notification_templates/', adminNotificationTemplate);
                })
                .then(({ data }) => {
                    adminNotificationTemplate = data;

                    return $http.post('/api/v2/inventory_scripts/', adminInventoryScript);
                })
                .then(({ data }) => {
                    adminInventoryScript = data;

                    return $http.post('/api/v2/projects/', adminProject);
                })
                .then(({ data }) => {
                    adminProject = data;

                    return $http.post('/api/v2/inventories/', adminSmartInventory);
                })
                .then(({ data }) => {
                    adminSmartInventory = data;

                    return $http.post('/api/v2/inventories/', adminStandardInventory);
                })
                .then(({ data }) => {
                    adminStandardInventory = data;
                    adminJobTemplate.inventory = data.id;

                    return $http.post('/api/v2/job_templates/', adminJobTemplate);
                })
                .then(({ data }) => {
                    adminJobTemplate = data;

                    return $http.post('/api/v2/users/', auditor);
                })
                .then(({ data }) => {
                    auditor = data;

                    return {
                        adminJobTemplate,
                        adminAWSCredential,
                        adminMachineCredential,
                        adminOrganization,
                        adminInventoryScript,
                        adminNotificationTemplate,
                        adminProject,
                        adminSmartInventory,
                        adminStandardInventory,
                        adminTeam,
                        adminUser,
                        auditor
                    };
                });
        },
        created => {
           store.created = created;

           client.login(store.auditor.username, store.auditor.password);

            done();
        });
    },
    'verify an auditor\'s credentials inputs are read-only': function (client) {
        navigateAndWaitForSpinner(client, `${credentials.url()}/${store.created.adminAWSCredential.id}/`);

        credentials.section.edit
            .expect.element('@title').text.contain(store.created.adminAWSCredential.name);

        credentials.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify an auditor\'s inventory scripts inputs are read-only': function (client) {
        navigateAndWaitForSpinner(client, `${inventoryScripts.url()}/${store.created.adminInventoryScript.id}/`);

        inventoryScripts.section.edit
            .expect.element('@title').text.contain(store.created.adminInventoryScript.name);

        inventoryScripts.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on inventory scripts form': function () {
        inventoryScripts.expect.element('@save').to.not.be.visible;
    },
    // TODO: re-enable these tests when JT edit has been re-factored to reliably show/remove the loading spinner
    // only one time.  Without this, we can't tell when all the requisite data is available.
    // 'verify an auditor\'s job template inputs are read-only': function (client) {
    //     navigateAndWaitForSpinner(client, `${templates.url()}/job_template/${store.created.adminJobTemplate.id}/`);
    //
    //     templates.section.editJobTemplate
    //         .expect.element('@title').text.contain(store.created.adminJobTemplate.name);
    //
    //     templates.section.edit.section.details.checkAllFieldsDisabled();
    // },
    // 'verify save button hidden from auditor on job templates form': function () {
    //     templates.expect.element('@save').to.not.be.visible;
    // },
    'verify an auditor\'s notification templates inputs are read-only': function (client) {
        navigateAndWaitForSpinner(client, `${notificationTemplates.url()}/${store.created.adminNotificationTemplate.id}/`);

        notificationTemplates.section.edit
            .expect.element('@title').text.contain(store.created.adminNotificationTemplate.name);

        notificationTemplates.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on notification templates page': function () {
        notificationTemplates.expect.element('@save').to.not.be.visible;
    },
    'verify an auditor\'s organizations inputs are read-only': function (client) {
        navigateAndWaitForSpinner(client, `${organizations.url()}/${store.created.adminOrganization.id}/`);

        organizations.section.edit
            .expect.element('@title').text.contain(store.created.adminOrganization.name);

        organizations.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on organizations form': function () {
        organizations.expect.element('@save').to.not.be.visible;
    },
    'verify an auditor\'s smart inventory inputs are read-only': function (client) {
        navigateAndWaitForSpinner(client, `${inventories.url()}/smart/${store.created.adminSmartInventory.id}/`);

        inventories.section.editSmartInventory
            .expect.element('@title').text.contain(store.created.adminSmartInventory.name);

        inventories.section.editSmartInventory.section.smartInvDetails.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on smart inventories form': function () {
        inventories.expect.element('@save').to.not.be.visible;
    },
    'verify an auditor\'s project inputs are read-only': function (client) {
        navigateAndWaitForSpinner(client, `${projects.url()}/${store.created.adminProject.id}/`);

        projects.section.edit
            .expect.element('@title').text.contain(store.created.adminProject.name);

        projects.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on projects form': function () {
        projects.expect.element('@save').to.not.be.visible;
    },
    'verify an auditor\'s standard inventory inputs are read-only': function (client) {
        navigateAndWaitForSpinner(client, `${inventories.url()}/inventory/${store.created.adminStandardInventory.id}/`);

        inventories.section.editStandardInventory
            .expect.element('@title').text.contain(store.created.adminStandardInventory.name);

        inventories.section.editStandardInventory.section.standardInvDetails.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on standard inventory form': function () {
        inventories.expect.element('@save').to.not.be.visible;
    },
    'verify an auditor\'s teams inputs are read-only': function (client) {
        navigateAndWaitForSpinner(client, `${teams.url()}/${store.created.adminTeam.id}/`);

        teams.section.edit
            .expect.element('@title').text.contain(store.created.adminTeam.name);

        teams.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on teams form': function () {
        teams.expect.element('@save').to.not.be.visible;
    },
    'verify an auditor\'s user inputs are read-only': function (client) {
        navigateAndWaitForSpinner(client, `${users.url()}/${store.created.adminUser.id}/`);

        users.section.edit
            .expect.element('@title').text.contain(store.created.adminUser.username);

        users.section.edit.section.details.checkAllFieldsDisabled();
    },
    'verify save button hidden from auditor on users form': function (client) {
        users.expect.element('@save').to.not.be.visible;

        client.end();
    }
};
