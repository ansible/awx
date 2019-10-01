import uuid from 'uuid';

import { AWX_E2E_PASSWORD } from './settings';

import {
    get,
    post,
} from './api';

const session = `e2e-${uuid().substr(0, 8)}`;
const store = {};

/* Utility function for accessing awx resources. This includes resources like
 * users, organizations, and job templates. Retrieves the end point, and creates
 * it if it does not exist.
 *
 * @param endpoint - The REST API url suffix.
 * @param data - Attributes used to create a new endpoint.
 * @param [unique] - An array of keys used to uniquely identify previously
 *     created resources from the endpoint.
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

/* Retrieves an organization, and creates it if it does not exist.
 *
 * @param [namespace] - A unique name prefix for the organization.
 *
 */
const getOrganization = (namespace = session) => getOrCreate('/organizations/', {
    name: `${namespace}-organization`,
    description: namespace
});

/* Retrieves an inventory, and creates it if it does not exist.
 * Also creates an organization with the same name prefix if needed.
 *
 * @param [namespace] - A unique name prefix for the inventory.
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

/* Identical to getInventory except it provides a unique suffix,
 * "*-inventory-nosource".
 *
 * @param[namespace] - A unique name prefix for the inventory.
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

/* Retrieves a host with the given name prefix, and creates it if it does not exist.
 * If an inventory does not exist with the same prefix, it is created as well.
 *
 * @param[namespace] - A unique name prefix for the host.
 */
const getHost = (namespace = session) => getInventory(namespace)
    .then(inventory => getOrCreate('/hosts/', {
        name: `${namespace}-host`,
        description: namespace,
        inventory: inventory.id,
        variables: JSON.stringify({ ansible_connection: 'local' }),
    }, ['name', 'inventory']));

/* Retrieves an inventory script with the given name prefix, and creates it if it
 * does not exist. If an organization does not exist with the same prefix, it is
 * created as well.
 *
 * @param[namespace] - A unique name prefix for the host.
 */
const getInventoryScript = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate('/inventory_scripts/', {
        name: `${namespace}-inventory-script`,
        description: namespace,
        organization: organization.id,
        script: '#!/usr/bin/env python'
    }));

/* Retrieves an inventory source, and creates it if it does not exist. If the
 * required dependent inventory and inventory script do not exist, they are also
 * created.
 *
 * @param[namespace] - A unique name prefix for the inventory source.
 */
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

/* Retrieves an AWS credential, and creates it if it does not exist.
 *
 * @param[namespace] - A unique name prefix for the AWS credential.
 */
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

/* Retrieves a machine credential, and creates it if it does not exist.
 *
 * @param[namespace] - A unique name prefix for the machine credential.
 */
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

/* Retrieves a team, and creates it if it does not exist.
 * If an organization does not exist with the same prefix, it is
 * created as well.
 *
 * @param[namespace] - A unique name prefix for the team.
 */
const getTeam = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate(`/organizations/${organization.id}/teams/`, {
        name: `${namespace}-team`,
        description: namespace,
        organization: organization.id,
    }));

/* Retrieves a smart inventory, and creates it if it does not exist.
 * name prefix. If an organization does not exist with the same prefix, it is
 * created as well.
 *
 * @param[namespace] - A unique name prefix for the smart inventory.
 */
const getSmartInventory = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate('/inventories/', {
        name: `${namespace}-smart-inventory`,
        description: namespace,
        organization: organization.id,
        host_filter: 'search=localhost',
        kind: 'smart'
    }));

/* Retrieves a notification template, and creates it if it does not exist.
 * name prefix. If an organization does not exist with the same prefix, it is
 * created as well.
 *
 * @param[namespace] - A unique name prefix for the notification template.
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

const waitForJob = endpoint => {
    const interval = 2000;
    const statuses = ['successful', 'failed', 'error', 'canceled'];

    let attempts = 30;

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

/* Retrieves a project, and creates it if it does not exist.
 * name prefix. If an organization does not exist with the same prefix, it is
 * created as well.
 *
 * @param[namespace] - A unique name prefix for the host.
 * @param[scmUrl] - The url of the repository.
 * @param[scmType] - The type of scm (git, etc.)
 */
const getProject = (
    namespace = session,
    scmUrl = 'https://github.com/ansible/ansible-tower-samples',
    scmType = 'git'
) => getOrganization(namespace)
    .then(organization => getOrCreate(`/organizations/${organization.id}/projects/`, {
        name: `${namespace}-project`,
        description: namespace,
        organization: organization.id,
        scm_url: `${scmUrl}`,
        scm_type: `${scmType}`
    }));

const getUpdatedProject = (namespace = session) => {
    const promises = [
        getProject(namespace),
    ];
    return Promise.all(promises)
        .then(([project]) =>
            post(`/api/v2/projects/${project.id}/update/`, {})
                .then(update => waitForJob(update.data.url))
                .then(() => getProject(namespace)));
};

/* Retrieves a job template, and creates it if it does not exist.
 * name prefix. This function also runs getOrCreate for an inventory,
 * credential, and project with the same prefix.
 *
 * @param [namespace] - Name prefix for associated dependencies.
 * @param [playbook] - Playbook for the job template.
 * @param [name] - Unique name prefix for the job template.
 * @param [updateProject] - Choose whether to sync the project with its repository.
 * */
const getJobTemplate = (
    namespace = session,
    playbook = 'hello_world.yml',
    name = `${namespace}-job-template`,
    updateProject = true,
    jobSliceCount = 1
) => {
    const promises = [
        getInventory(namespace),
        getAdminMachineCredential(namespace),
    ];
    if (updateProject) {
        promises.push(getUpdatedProject(namespace));
    } else {
        promises.push(getProject(namespace));
    }

    return Promise.all(promises)
        .then(([inventory, credential, project]) => getOrCreate('/job_templates/', {
            name: `${name}`,
            description: namespace,
            inventory: inventory.id,
            credential: credential.id,
            project: project.id,
            playbook: `${playbook}`,
            job_slice_count: `${jobSliceCount}`,
        }));
};

/* Similar to getJobTemplate, except that it also launches the job.
 *
 * @param[namespace] - A unique name prefix for the job and its dependencies.
 * @param[playbook] - The playbook file to be run by the job template.
 * @param[name] - A unique name for the job template.
 * @param[wait] - Choose whether to return the result of the completed job.
 */
const getJob = (
    namespace = session,
    playbook = 'hello_world.yml',
    name = `${namespace}-job-template`,
    wait = true
) => getJobTemplate(namespace, playbook, name)
    .then(template => {
        const launchURL = template.related.launch;
        return post(launchURL, {}).then(response => {
            const jobURL = response.data.url;
            if (wait) {
                return waitForJob(jobURL).then(() => response.data);
            }
            return response.data;
        });
    });

/* Retrieves a workflow template, and creates it if it does not exist.
 * name prefix. If an organization does not exist with the same prefix, it is
 * created as well. A basic workflow node setup is also created.
 *
 * @param[namespace] - A unique name prefix for the workflow template.
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

/* Retrieves a auditor user, and creates it if it does not exist.
 * name prefix. If an organization does not exist with the same prefix,
 * it is also created.
 *
 * @param[namespace] - A unique name prefix for the auditor.
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

/* Retrieves a user, and creates it if it does not exist.
 * name prefix. If an organization does not exist with the same prefix,
 * it is also created.
 *
 * @param[namespace] - A unique name prefix for the user's organization.
 * @param[username] - A unique name for the user.
 */
const getUser = (
    namespace = session,
    // unique substrings are needed to avoid the edge case
    // where a user and org both exist, but the user is not in the organization.
    // this ensures a new user is always created.
    username = `user-${uuid().substr(0, 8)}`,
    password = AWX_E2E_PASSWORD,
    isSuperuser = false,
    isSystemAuditor = false,
    email = `email-${uuid().substr(0, 8)}@example.com`,
    firstName = `first-name-${uuid().substr(0, 8)}`,
    lastName = `last-name-${uuid().substr(0, 8)}`
) => getOrganization(namespace)
    .then(organization => getOrCreate(`/organizations/${organization.id}/users/`, {
        email,
        first_name: firstName,
        is_superuser: isSuperuser,
        is_system_auditor: isSystemAuditor,
        last_name: lastName,
        organization: organization.id,
        password,
        username,
    }, ['username']));

/* Retrieves a job template admin, and creates it if it does not exist.
 * If a job template or organization does not exist with the same
 * prefix, they are also created.
 *
 * @param[namespace] - A unique name prefix for the template admin.
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

/* Retrieves a project admin, and creates it if it does not exist.
 * If a job template or organization does not exist with the same
 * prefix, they are also created.
 *
 * @param[namespace] - A unique name prefix for the project admin.
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

/* Retrieves a inventory source schedule, and creates it if it does not exist.
 * If an inventory source does not exist with the same prefix, it is also created.
 *
 * @param[namespace] - A unique name prefix for the schedule.
 */
const getInventorySourceSchedule = (namespace = session) => getInventorySource(namespace)
    .then(source => getOrCreate(source.related.schedules, {
        name: `${source.name}-schedule`,
        description: namespace,
        rrule: 'DTSTART:20171104T040000Z RRULE:FREQ=DAILY;INTERVAL=1;COUNT=1'
    }));

/* Retrieves a job template schedule, and creates it if it does not exist.
 * If an job template  does not exist with the same prefix, it is also created.
 *
 * @param[namespace] - A unique name prefix for the schedule.
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
    getWorkflowTemplate,
};
