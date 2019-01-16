import uuid from 'uuid';

import { AWX_E2E_PASSWORD } from './settings';

import {
    get,
    post,
} from './api';

const session = `e2e-${uuid().substr(0, 8)}`;
const store = {};

/* Utility function for accessing awx resources. This includes resources like
 * users, organizations, and job templates. Creates the resource if it does
 * not already exist, then returns it.
 *
 * @param endpoint - The REST API url suffix.
 * @param data - Attributes used to create a new endpoint.
 * @param [unique=['name']] - An array of keys used to uniquely identify previously created resources from the endpoint.
 *
 */
const getOrCreate = (endpoint, data, unique = ['name']) => {
    const identifiers = Object.keys(data).filter(key => unique.indexOf(key) > -1);

    if (identifiers.length < 1) {
        throw new Error('A unique key value must be provided.');
    }

    const lookup = `${endpoint}/${identifiers.map(key => data[key]).join('-')}`;
    const params = Object.assign(...identifiers.map(key => ({ [key]: data[key] })));

    store[lookup] = store[lookup] || get(endpoint, { params })
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

    return store[lookup].then(created => created.data);
};

/* Creates an organization if one does not already exist, and returns it.
 *
 * @param [namespace=session] - A unique name prefix for the organization.
 *
 */
const getOrganization = (namespace = session) => getOrCreate('/organizations/', {
    name: `${namespace}-organization`,
    description: namespace
});

/* Creates an inventory if one does not already exist, and returns it.
 * Also creates an organization with the same name prefix if needed.
 *
 * @param [namespace=session] - A unique name prefix for the inventory.
 *
 */
const getInventory = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate('/inventories/', {
        name: `${namespace}-inventory`,
        description: namespace,
        organization: organization.id
    }).then(inventory => getOrCreate('/hosts/', {
        name: `${namespace}-host`,
        description: namespace,
        inventory: inventory.id,
        variables: JSON.stringify({ ansible_connection: 'local' }),
    }, ['name', 'inventory']).then(() => inventory)));

/* Identical to getInventory except it provides a unique suffix, "*-inventory-nosource".
 *
 * @param[namespace=session] - A unique name prefix for the inventory.
*/
const getInventoryNoSource = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate('/inventories/', {
        name: `${namespace}-inventory-nosource`,
        description: namespace,
        organization: organization.id
    }).then(inventory => getOrCreate('/hosts/', {
        name: `${namespace}-host`,
        description: namespace,
        inventory: inventory.id,
        variables: JSON.stringify({ ansible_connection: 'local' }),
    }, ['name', 'inventory']).then(() => inventory)));

/* Gets or, if it does not exist, creates an host with the given name prefix.
 * If an inventory does not exist with the same prefix, it is created as well.
 *
 * @param[namespace=session] - A unique name prefix for the host.
 */
const getHost = (namespace = session) => getInventory(namespace)
    .then(inventory => getOrCreate('/hosts/', {
        name: `${namespace}-host`,
        description: namespace,
        inventory: inventory.id,
        variables: JSON.stringify({ ansible_connection: 'local' }),
    }, ['name', 'inventory']));

/* Gets or, if it does not exist, creates an inventory script  with the given
 * name prefix. If an organization does not exist with the same prefix, it is
 * created as well.
 *
 * @param[namespace=session] - A unique name prefix for the host.
 */
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

    return Promise.all(promises)
        .then(([inventory, inventoryScript]) => getOrCreate('/inventory_sources/', {
            name: `${namespace}-inventory-source-custom`,
            description: namespace,
            source: 'custom',
            inventory: inventory.id,
            source_script: inventoryScript.id
        }));
};

const getAdminAWSCredential = (namespace = session) => {
    const promises = [
        get('/me/'),
        getOrCreate('/credential_types/', {
            name: 'Amazon Web Services'
        })
    ];

    return Promise.all(promises)
        .then(([me, credentialType]) => {
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
        });
};

const getAdminMachineCredential = (namespace = session) => {
    const promises = [
        get('/me/'),
        getOrCreate('/credential_types/', { name: 'Machine' })
    ];

    return Promise.all(promises)
        .then(([me, credentialType]) => {
            const [admin] = me.data.results;
            return getOrCreate('/credentials/', {
                name: `${namespace}-credential-machine-admin`,
                description: namespace,
                credential_type: credentialType.id,
                user: admin.id
            });
        });
};

/* Gets or, if it does not exist, creates a team with the given
 * name prefix. If an organization does not exist with the same prefix, it is
 * created as well.
 *
 * @param[namespace=session] - A unique name prefix for the team.
 */
const getTeam = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate(`/organizations/${organization.id}/teams/`, {
        name: `${namespace}-team`,
        description: namespace,
        organization: organization.id,
    }));

/* Gets or, if it does not exist, creates a smart inventory with the given
 * name prefix. If an organization does not exist with the same prefix, it is
 * created as well.
 *
 * @param[namespace=session] - A unique name prefix for the smart inventory.
 */
const getSmartInventory = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate('/inventories/', {
        name: `${namespace}-smart-inventory`,
        description: namespace,
        organization: organization.id,
        host_filter: 'search=localhost',
        kind: 'smart'
    }));

/* Gets or, if it does not exist, creates a notification template with the given
 * name prefix. If an organization does not exist with the same prefix, it is
 * created as well.
 *
 * @param[namespace=session] - A unique name prefix for the notification template.
 */
const getNotificationTemplate = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate(`/organizations/${organization.id}/notification_templates/`, {
        name: `${namespace}-notification-template`,
        description: namespace,
        organization: organization.id,
        notification_type: 'slack',
        notification_configuration: {
            token: '54321GFEDCBAABCDEFG12345',
            channels: ['awx-e2e']
        }
    }));

/* Gets or, if it does not exist, creates a project with the given
 * name prefix. If an organization does not exist with the same prefix, it is
 * created as well.
 *
 * @param[namespace=session] - A unique name prefix for the host.
 */
const getProject = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate(`/organizations/${organization.id}/projects/`, {
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

/* Gets or, if it does not exist, creates a job template with the given
 * name prefix. This function also runs getOrCreate for an inventory,
 * credential, and project with the same prefix.
 *
 * @param[namespace=session] - A unique name prefix for the job template.
 */
const getJobTemplate = (namespace = session) => {
    const promises = [
        getInventory(namespace),
        getAdminMachineCredential(namespace),
        getUpdatedProject(namespace)
    ];

    return Promise.all(promises)
        .then(([inventory, credential, project]) => getOrCreate('/job_templates/', {
            name: `${namespace}-job-template`,
            description: namespace,
            inventory: inventory.id,
            credential: credential.id,
            project: project.id,
            playbook: 'hello_world.yml',
        }));
};

/* Similar to getJobTemplate, except that it also launches the job.
 *
 * @param[namespace=session] - A unique name prefix for the host.
 */
const getJob = (namespace = session) => getJobTemplate(namespace)
    .then(template => {
        const launchURL = template.related.launch;
        return post(launchURL, {}).then(response => {
            const jobURL = response.data.url;
            return waitForJob(jobURL).then(() => response.data);
        });
    });

/* Gets or, if it does not exist, creates a workflow template with the given
 * name prefix. If an organization does not exist with the same prefix, it is
 * created as well. A basic workflow node setup is also created.
 *
 * @param[namespace=session] - A unique name prefix for the workflow template.
 */
const getWorkflowTemplate = (namespace = session) => {
    const workflowTemplatePromise = getOrganization(namespace)
        .then(organization => getOrCreate(`/organizations/${organization.id}/workflow_job_templates/`, {
            name: `${namespace}-workflow-template`,
            organization: organization.id,
            variables: '---',
            extra_vars: '',
        }));

    const resources = [
        workflowTemplatePromise,
        getInventorySource(namespace),
        getUpdatedProject(namespace),
        getJobTemplate(namespace),
    ];

    const workflowNodePromise = Promise.all(resources)
        .then(([workflowTemplate, source, project, jobTemplate]) => {
            const workflowNodes = workflowTemplate.related.workflow_nodes;
            const unique = 'unified_job_template';

            const nodes = [
                getOrCreate(workflowNodes, { [unique]: project.id }, [unique]),
                getOrCreate(workflowNodes, { [unique]: jobTemplate.id }, [unique]),
                getOrCreate(workflowNodes, { [unique]: source.id }, [unique]),
            ];

            const createSuccessNodes = ([projectNode, jobNode, sourceNode]) => Promise.all([
                getOrCreate(projectNode.related.success_nodes, { id: jobNode.id }, ['id']),
                getOrCreate(jobNode.related.success_nodes, { id: sourceNode.id }, ['id']),
            ]);

            return Promise.all(nodes)
                .then(createSuccessNodes);
        });

    return Promise.all([workflowTemplatePromise, workflowNodePromise])
        .then(([workflowTemplate, nodes]) => workflowTemplate);
};

/* Gets or, if it does not exist, creates a auditor user with the given
 * name prefix. If an organization does not exist with the same prefix,
 * it is also created.
 *
 * @param[namespace=session] - A unique name prefix for the project admin.
 */
const getAuditor = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate(`/organizations/${organization.id}/users/`, {
        username: `auditor-${uuid().substr(0, 8)}`,
        organization: organization.id,
        first_name: 'auditor',
        last_name: 'last',
        email: 'null@ansible.com',
        is_superuser: false,
        is_system_auditor: true,
        password: AWX_E2E_PASSWORD
    }, ['username']));

const getUser = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate(`/organizations/${organization.id}/users/`, {
        username: `user-${uuid().substr(0, 8)}`,
        organization: organization.id,
        first_name: 'firstname',
        last_name: 'lastname',
        email: 'null@ansible.com',
        is_superuser: false,
        is_system_auditor: false,
        password: AWX_E2E_PASSWORD
    }, ['username']));

const getUserExact = (namespace = session, name) => getOrganization(namespace)
    .then(organization => getOrCreate(`/organizations/${organization.id}/users/`, {
        username: `${name}`,
        organization: organization.id,
        first_name: 'firstname',
        last_name: 'lastname',
        email: 'null@ansible.com',
        is_superuser: false,
        is_system_auditor: false,
        password: AWX_E2E_PASSWORD
    }, ['username']));

/* Gets or, if it does not exist, creates a job template  admin with the given
 * name prefix. If a job template or organization does not exist with the same
 * prefix, they are also created.
 *
 * @param[namespace=session] - A unique name prefix for the project admin.
 */
const getJobTemplateAdmin = (namespace = session) => {
    const rolePromise = getJobTemplate(namespace)
        .then(obj => obj.summary_fields.object_roles.admin_role);

    const userPromise = getOrganization(namespace)
        .then(obj => getOrCreate(`/organizations/${obj.id}/users/`, {
            username: `job-template-admin-${uuid().substr(0, 8)}`,
            organization: obj.id,
            first_name: 'firstname',
            last_name: 'lastname',
            email: 'null@ansible.com',
            is_superuser: false,
            is_system_auditor: false,
            password: AWX_E2E_PASSWORD
        }, ['username']));

    const assignRolePromise = Promise.all([userPromise, rolePromise])
        .then(([user, role]) => post(`/api/v2/roles/${role.id}/users/`, { id: user.id }));

    return Promise.all([userPromise, assignRolePromise])
        .then(([user, assignment]) => user);
};

/* Gets or, if it does not exist, creates a project admin with the given
 * name prefix. If a project or organization does not exist with the same
 * prefix, they are also created.
 *
 * @param[namespace=session] - A unique name prefix for the project admin.
 */
const getProjectAdmin = (namespace = session) => {
    const rolePromise = getUpdatedProject(namespace)
        .then(obj => obj.summary_fields.object_roles.admin_role);

    const userPromise = getOrganization(namespace)
        .then(obj => getOrCreate(`/organizations/${obj.id}/users/`, {
            username: `project-admin-${uuid().substr(0, 8)}`,
            organization: obj.id,
            first_name: 'firstname',
            last_name: 'lastname',
            email: 'null@ansible.com',
            is_superuser: false,
            is_system_auditor: false,
            password: AWX_E2E_PASSWORD
        }, ['username']));

    const assignRolePromise = Promise.all([userPromise, rolePromise])
        .then(([user, role]) => post(`/api/v2/roles/${role.id}/users/`, { id: user.id }));

    return Promise.all([userPromise, assignRolePromise])
        .then(([user, assignment]) => user);
};

const getInventorySourceSchedule = (namespace = session) => getInventorySource(namespace)
    .then(source => getOrCreate(source.related.schedules, {
        name: `${source.name}-schedule`,
        description: namespace,
        rrule: 'DTSTART:20171104T040000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1'
    }));

/* Gets or, if it does not exist, creates a job template schedule with the given
 * name prefix. If a job template does not exist with the same prefix, it is
 * created as well.
 *
 * @param[namespace=session] - A unique name prefix for the schedule.
 */
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
    getHost,
    getInventory,
    getInventoryNoSource,
    getInventoryScript,
    getInventorySource,
    getInventorySourceSchedule,
    getJob,
    getJobTemplate,
    getJobTemplateAdmin,
    getJobTemplateSchedule,
    getNotificationTemplate,
    getOrganization,
    getOrCreate,
    getProject,
    getProjectAdmin,
    getSmartInventory,
    getTeam,
    getUpdatedProject,
    getUser,
    getUserExact,
    getWorkflowTemplate,
};
