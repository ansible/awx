import uuid from 'uuid';

import {
    get,
    post,
} from '../api';
import {
    getAdminMachineCredential,
    getInventory,
    getOrCreate,
    getOrganization,
    waitForJob,
} from '../fixtures';

// AWX_E2E_URL='https://localhost:3000' npm --prefix awx/ui run e2e -- --filter="*jobz*"

const session = `e2e-${uuid().substr(0, 8)}`;

const SCM_URL = 'https://github.com/jakemcdermott/ansible-playbooks';
const PLAYBOOK = 'setfact_50.yml';
const PARAMS = '?job_event_search=page_size:200;order_by:start_line;not__event__in:playbook_on_start,playbook_on_play_start,playbook_on_task_start,playbook_on_stats;task:set';

let data;

const waitForJobz = endpoint => {
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

const getProject = (namespace = session) => getOrganization(namespace)
    .then(organization => getOrCreate('/projects/', {
        name: `${namespace}-project`,
        description: namespace,
        organization: organization.id,
        scm_url: SCM_URL,
        scm_type: 'git'
    })
    .then(project => {
        if (project.related.current_update) {
            return waitForJobz(project.related.current_update)
                .then(() => project);
        }
        return project;
    }));

const getJobTemplate = (namespace = session) => {
    const promises = [
        getInventory(namespace),
        getAdminMachineCredential(namespace),
        getProject(namespace)
    ];

    return Promise.all(promises)
        .then(([inventory, credential, project]) => getOrCreate('/job_templates/', {
            name: `${namespace}-job-template`,
            description: namespace,
            inventory: inventory.id,
            credential: credential.id,
            project: project.id,
            playbook: PLAYBOOK,
        }));
};

const getJob = (namespace = session) => getJobTemplate(namespace)
    .then(template => {
        if (template.related.last_job) {
            return waitForJobz(template.related.last_job);
        }

        return post(template.related.launch, {})
            .then(res => waitForJobz(res.data.url));
    });

module.exports = {
    before: (client, done) => {
        getJob()
            .then(job => {
                data = { job };
                done();
            })
    },
    'test jobz': client => {
        const location = `${client.globals.launch_url}/#/jobz/playbook/${data.job.id}`;
        const templates = client.page.templates();

        client.useCss();
        client.resizeWindow(1200, 800);
        client.login();
        client.waitForAngular();

        // client.url(location);
        client.url(`${location}${PARAMS}`);

        client.pause();

        client.end();
    },
};
