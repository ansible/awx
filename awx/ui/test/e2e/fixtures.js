import uuid from 'uuid';

import { AWX_E2E_PASSWORD } from './settings';

import {
    all,
    get,
    post,
    spread
} from './api';

const session = `e2e-${uuid().substr(0, 8)}`;

const store = {};

const getOrCreate = (endpoint, data) => {
    const identifier = Object.keys(data).find(key => ['name', 'username'].includes(key));

    if (identifier === undefined) {
        throw new Error('A unique key value must be provided.');
    }

    const identity = data[identifier];

    if (store[endpoint] && store[endpoint][identity]) {
        return store[endpoint][identity].then(created => created.data);
    }

    if (!store[endpoint]) {
        store[endpoint] = {};
    }

    const query = { params: { [identifier]: identity } };

    store[endpoint][identity] = get(endpoint, query)
        .then(res => {
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

const getOrganization = (namespace = session) => getOrCreate('/organizations/', {
    name: `${namespace}-organization`,
    description: namespace
});

const getInventory = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate('/inventories/', {
        name: `${namespace}-inventory`,
        description: namespace,
        organization: organization.id,
    }).then(inventory => getOrCreate('/hosts/', {
        name: `${namespace}-host`,
        description: namespace,
        inventory: inventory.id,
        variables: JSON.stringify({ ansible_connection: 'local' }),
    }).then(() => inventory)));

const getHost = (namespace = session) => getInventory(namespace)
    .then(inventory => getOrCreate('/hosts/', {
        name: `${namespace}-host`,
        description: namespace,
        inventory: inventory.id,
        variables: JSON.stringify({ ansible_connection: 'local' }),
    }).then((host) => host));

const getInventoryScript = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate('/inventory_scripts/', {
        name: `${namespace}-inventory-script`,
        description: namespace,
        organization: organization.id,
        script: '#!/usr/bin/env python'
    }));

const getInventorySource = (namespace = session) => {
    const promises = [
        getInventory(namespace),
        getInventoryScript(namespace)
    ];

    return all(promises)
        .then(spread((inventory, inventoryScript) => getOrCreate('/inventory_sources/', {
            name: `${namespace}-inventory-source-custom`,
            description: namespace,
            source: 'custom',
            inventory: inventory.id,
            source_script: inventoryScript.id
        })));
};

const getAdminAWSCredential = (namespace = session) => {
    const promises = [
        get('/me/'),
        getOrCreate('/credential_types/', {
            name: 'Amazon Web Services'
        })
    ];

    return all(promises)
        .then(spread((me, credentialType) => {
            const [admin] = me.data.results;

            return getOrCreate('/credentials/', {
                name: `${namespace}-credential-aws`,
                description: namespace,
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

const getAdminMachineCredential = (namespace = session) => {
    const promises = [
        get('/me/'),
        getOrCreate('/credential_types/', { name: 'Machine' })
    ];

    return all(promises)
        .then(spread((me, credentialType) => {
            const [admin] = me.data.results;

            return getOrCreate('/credentials/', {
                name: `${namespace}-credential-machine-admin`,
                description: namespace,
                credential_type: credentialType.id,
                user: admin.id
            });
        }));
};

const getTeam = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate('/teams/', {
        name: `${namespace}-team`,
        description: namespace,
        organization: organization.id,
    }));

const getSmartInventory = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate('/inventories/', {
        name: `${namespace}-smart-inventory`,
        description: namespace,
        organization: organization.id,
        host_filter: 'search=localhost',
        kind: 'smart'
    }));

const getNotificationTemplate = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate('/notification_templates/', {
        name: `${namespace}-notification-template`,
        description: namespace,
        organization: organization.id,
        notification_type: 'slack',
        notification_configuration: {
            token: '54321GFEDCBAABCDEFG12345',
            channels: ['awx-e2e']
        }
    }));

const getProject = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate('/projects/', {
        name: `${namespace}-project`,
        description: namespace,
        organization: organization.id,
        scm_url: 'https://github.com/ansible/ansible-tower-samples',
        scm_type: 'git'
    }));

const waitForJob = endpoint => {
    const interval = 2000;
    const statuses = ['successful', 'failed', 'error', 'canceled'];

    let attempts = 20;

    return new Promise((resolve, reject) => {
        (function pollStatus () {
            get(endpoint).then(update => {
                const completed = statuses.indexOf(update.data.status) > -1;

                if (completed) {
                    return resolve(update.data);
                }

                if (--attempts <= 0) {
                    return reject(new Error('Retry limit exceeded.'));
                }

                return setTimeout(pollStatus, interval);
            });
        }());
    });
};

const getUpdatedProject = (namespace = session) => getProject(namespace)
    .then(project => {
        const updateURL = project.related.current_update;

        if (updateURL) {
            return waitForJob(updateURL).then(() => project);
        }

        return project;
    });

const getJob = (namespace = session) => getJobTemplate(namespace)
    .then(template => {
        const launchURL = template.related.launch;
        return post(launchURL, {}).then(response => {
            const jobURL = response.data.url;
            return waitForJob(jobURL).then(() => response.data);
        });
    });

const getJobTemplate = (namespace = session) => {
    const promises = [
        getInventory(namespace),
        getAdminMachineCredential(namespace),
        getUpdatedProject(namespace)
    ];

    return all(promises)
        .then(spread((inventory, credential, project) => getOrCreate('/job_templates/', {
            name: `${namespace}-job-template`,
            description: namespace,
            inventory: inventory.id,
            credential: credential.id,
            project: project.id,
            playbook: 'hello_world.yml',
        })));
};

const getAuditor = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate('/users/', {
        username: `auditor-${uuid().substr(0, 8)}`,
        organization: organization.id,
        first_name: 'auditor',
        last_name: 'last',
        email: 'null@ansible.com',
        is_superuser: false,
        is_system_auditor: true,
        password: AWX_E2E_PASSWORD
    }));

const getUser = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate('/users/', {
        username: `user-${uuid().substr(0, 8)}`,
        organization: organization.id,
        first_name: 'firstname',
        last_name: 'lastname',
        email: 'null@ansible.com',
        is_superuser: false,
        is_system_auditor: false,
        password: AWX_E2E_PASSWORD
    }));

const getJobTemplateAdmin = (namespace = session) => {
    const rolePromise = getJobTemplate(namespace)
        .then(obj => obj.summary_fields.object_roles.admin_role);

    const userPromise = getOrganization(namespace)
        .then(obj => getOrCreate('/users/', {
            username: `job-template-admin-${uuid().substr(0, 8)}`,
            organization: obj.id,
            first_name: 'firstname',
            last_name: 'lastname',
            email: 'null@ansible.com',
            is_superuser: false,
            is_system_auditor: false,
            password: AWX_E2E_PASSWORD
        }));

    const assignRolePromise = Promise.all([userPromise, rolePromise])
        .then(spread((user, role) => post(`/api/v2/roles/${role.id}/users/`, { id: user.id })));

    return Promise.all([userPromise, assignRolePromise])
        .then(spread(user => user));
};

const getInventorySourceSchedule = (namespace = session) => getInventorySource(namespace)
    .then(source => getOrCreate(source.related.schedules, {
        name: `${source.name}-schedule`,
        description: namespace,
        rrule: 'DTSTART:20171104T040000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1'
    }));

const getJobTemplateSchedule = (namespace = session) => getJobTemplate(namespace)
    .then(template => getOrCreate(template.related.schedules, {
        name: `${template.name}-schedule`,
        description: namespace,
        rrule: 'DTSTART:20351104T040000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1'
    }));

module.exports = {
    getAdminAWSCredential,
    getAdminMachineCredential,
    getAuditor,
    getInventory,
    getInventoryScript,
    getInventorySource,
    getInventorySourceSchedule,
    getJobTemplate,
    getJobTemplateAdmin,
    getJobTemplateSchedule,
    getNotificationTemplate,
    getOrCreate,
    getOrganization,
    getSmartInventory,
    getTeam,
    getUpdatedProject,
    getUser,
    getJob,
    getHost,
};
