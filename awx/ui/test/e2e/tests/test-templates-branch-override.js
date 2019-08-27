import uuid from 'uuid';

import {
    getJobTemplate,
    getProject
} from '../fixtures';

import {
    AWX_E2E_URL
} from '../settings';

const testID = uuid().substr(0, 8);
const namespace = `branch-override-${testID}`;

let data;

module.exports = {
    before: (client, done) => {
        const resources = [
            getProject(namespace, 'https://github.com/ansible/test-playbooks.git'),
            getJobTemplate(namespace, 'debug.yml')
        ];
        Promise.all(resources)
            .then(([project, jt]) => {
                data = { project, jt };
                client
                    .login()
                    .waitForAngular();
                done();
            });
    },
    'test a job template with branch override': client => {
        // project page
        client
            .navigateTo(`${AWX_E2E_URL}/#/projects/${data.project.id}`, false)
            .waitForAngular()
            .waitForElementVisible('#project_allow_override_chbox_3:enabled')
            .click('#project_allow_override_chbox_3')
            .click('#project_save_btn')
            .waitForElementPresent('#project_form[class*=ng-pristine]')
            .assert.cssClassPresent('#project_allow_override_chbox_3', 'ng-not-empty');
        // template form and launch
        client
            .navigateTo(`${AWX_E2E_URL}/#/templates/job_template/${data.jt.id}`, false)
            .waitForAngular()
            .waitForElementVisible('#job_template_scm_branch')
            .setValue('#job_template_scm_branch', 'empty_branch')
            .waitForElementVisible('#select2-playbook-select-container')
            .click('#select2-playbook-select-container')
            .setValue(
                '#job_template_playbook_group .select2-search__field',
                ['assert_on_this_branch.yml', client.Keys.ENTER]
            )
            .waitForElementPresent('#job_template_form[class*=ng-dirty]')
            .waitForElementPresent('#job_template_save_btn:enabled')
            .click('#job_template_save_btn')
            .waitForSpinny()
            .waitForElementPresent('#job_template_form[class*=ng-pristine]')
            .waitForElementPresent('#job_template_controls .at-LaunchTemplate button:enabled')
            .click('#job_template_controls .at-LaunchTemplate button')
            .waitForElementVisible('[ng-if="vm.scmBranch"]');
        client.expect.element('[ng-if="vm.scmBranch"] .JobResults-resultRowText')
            .text.to.equal('empty_branch');
        client.expect.element('[ng-if="vm.playbook"] .JobResults-resultRowText')
            .text.to.equal('assert_on_this_branch.yml');
        client.waitForElementVisible('span .icon-job-successful', 60000);
    },
    after: client => {
        client.end();
    }
};
