import uuid from 'uuid';

import {
    all,
    get,
    post,
    spread
} from './api.js';


const sid = uuid().substr(0,8);

let store = {};


const getOrCreate = function(endpoint, data) {
    let identifier = Object.keys(data).find(key => ['name', 'username'].includes(key));

    if (identifier === undefined) {
        throw new Error('A unique key value must be provided.');
    }

    let identity = data[identifier];

    if (store[endpoint] && store[endpoint][identity]) {
        return store[endpoint][identity].then(created => created.data);
    }

    if (!store[endpoint]) {
        store[endpoint] = {};
    }

    let query = { params: { [identifier]: identity } };

    store[endpoint][identity] = get(endpoint, query).then(res => {

        if (res.data.results.length > 1) {
            return Promise.reject(new Error('More than one matching result.'));
        }

        if (res.data.results.length === 1) {
            return get(res.data.results[0].url);
        }

        if (res.data.results.length === 0) {
            return post(endpoint, data);
        }

        return Promise.reject(new Error(`unexpected response: ${res}`));
    });

    return store[endpoint][identity].then(created => created.data);
};


const getOrganization = function() {
    return getOrCreate('/organizations/', {
        name: `e2e-organization-${sid}`
    });
};


const getInventory = function() {
    return getOrganization().then(organization => {
        return getOrCreate('/inventories/', {
            name: `e2e-inventory-${sid}`,
            organization: organization.id
        });
    });
};


const getInventoryScript = function() {
    return getOrganization().then(organization => {
        return getOrCreate('/inventory_scripts/', {
            name: `e2e-inventory-script-${sid}`,
            organization: organization.id,
            script: '#!/usr/bin/env python'
        });
    });
};


const getAdminAWSCredential = function() {
    return all([
        get('/me/'),
        getOrCreate('/credential_types/', {
            name: "Amazon Web Services"
        })
    ])
    .then(spread((me, credentialType) => {
        let admin = me.data.results[0];
        return getOrCreate('/credentials/', {
            name: `e2e-aws-credential-${sid}`,
            credential_type: credentialType.id,
            user: admin.id,
            inputs: {
                username: 'admin',
                password: 'password',
                security_token: 'AAAAAAAAAAAAAAAA'
            }
        });
    }));
};


const getAdminMachineCredential = function() {
    return all([
        get('/me/'),
        getOrCreate('/credential_types/', { name: "Machine" })
    ])
    .then(spread((me, credentialType) => {
        let admin = me.data.results[0];
        return getOrCreate('/credentials/', {
            name: `e2e-machine-credential-${sid}`,
            credential_type: credentialType.id,
            user: admin.id
        });
    }));
};


const getTeam = function() {
    return getOrganization().then(organization => {
        return getOrCreate('/teams/', {
            name: `e2e-team-${sid}`,
            organization: organization.id,
        });
    });
};


const getSmartInventory = function() {
    return getOrganization().then(organization => {
        return getOrCreate('/inventories/', {
            name: `e2e-smart-inventory-${sid}`,
            organization: organization.id,
            host_filter: 'search=localhost',
            kind: 'smart'
        });
    });
};


const getNotificationTemplate = function() {
    return getOrganization().then(organization => {
        return getOrCreate('/notification_templates/', {
            name: `e2e-notification-template-${sid}`,
            organization: organization.id,
            notification_type: 'slack',
            notification_configuration: {
                token: '54321GFEDCBAABCDEFG12345',
                channels: ['awx-e2e']
            }
        });
    });
};


const getProject = function() {
    return getOrganization().then(organization => {
        return getOrCreate('/projects/', {
            name: `e2e-project-${sid}`,
            organization: organization.id,
            scm_url: 'https://github.com/ansible/ansible-tower-samples',
            scm_type: 'git'
        });
    });
};


const waitForJob = function(endpoint) {
    const interval = 2000;
    const statuses = ['successful', 'failed', 'error', 'canceled'];

    let attempts = 20;

    return new Promise((resolve, reject) => {
        (function pollStatus() {            
            get(endpoint).then(update => {
                let completed = statuses.indexOf(update.data.status) > -1;
                if (completed) return resolve();
                if (--attempts <= 0) return reject('Retry limit exceeded.');
                setTimeout(pollStatus, interval);
            });
        })();
    });
};


const getUpdatedProject = function() {
    return getProject().then(project => {
        let updateURL = project.related.current_update;
        if (updateURL) {
            return waitForJob(updateURL).then(() => project);
        }
        return project;
    });
};


const getJobTemplate = function() {
    return all([
        getInventory(),
        getAdminMachineCredential(),
        getUpdatedProject()
    ])
    .then(spread((inventory, credential, project) => {
        return getOrCreate('/job_templates', {
            name: `e2e-job-template-${sid}`,
            inventory: inventory.id,
            credential: credential.id,
            project: project.id,
            playbook: 'hello_world.yml'
        });
    }));
};


const getAuditor = function() {
    return getOrganization().then(organization => {
        return getOrCreate('/users/', {
            organization: organization.id,
            username: `e2e-auditor-${sid}`,
            first_name: 'auditor',
            last_name: 'last',
            email: 'null@ansible.com',
            is_superuser: false,
            is_system_auditor: true,
            password: 'password'
        })
    });
};


const getUser = function() {
    return getOrCreate('/users/', {
        username: `e2e-user-${sid}`,
        first_name: `user-${sid}-first`,
        last_name: `user-${sid}-last`,
        email: `null-${sid}@ansible.com`,
        is_superuser: false,
        is_system_auditor: false,
        password: 'password'
    });
};


module.exports = {
    getAdminAWSCredential,
    getAdminMachineCredential,
    getAuditor,
    getInventory,
    getInventoryScript,
    getJobTemplate,
    getNotificationTemplate,
    getOrCreate,
    getOrganization,
    getSmartInventory,
    getTeam,
    getUpdatedProject,
    getUser
};
