import {
    getJobTemplate,
    getUpdatedProject,
} from '../fixtures';

import {
    AWX_E2E_TIMEOUT_MEDIUM,
} from '../settings';

const namespace = 'test-pagination';

module.exports = {

    before: (client, done) => {
        const resources = [getUpdatedProject(namespace)];

        Promise.all(resources)
            .then(() => {
                for (let i = 0; i < 25; i++) {
                    // Create enough job templates to make at least 2 pages of data
                    resources.push(getJobTemplate(namespace, 'hello_world.yml', `${namespace}-job-template-${i}`, false));
                }
                Promise.all(resources)
                    .then(() => done());
            });

        client
            .login()
            .waitForAngular();
    },
    'Test job template pagination': client => {
        client
            .useCss()
            .findThenClick('[ui-sref="templates"]', 'css')
            .waitForElementVisible('.SmartSearch-input')
            .clearValue('.SmartSearch-input');
        const firstRow = client
            .getText('#templates_list .at-RowItem-header >  a:nth-of-type(1)');
        client.findThenClick('.Paginate-controls--next', 'css');
        client.expect.element('#templates_list .at-RowItem-header >  a:nth-of-type(1)')
            .to.have.value.not.equals(firstRow).before(AWX_E2E_TIMEOUT_MEDIUM);
        client.findThenClick('.Paginate-controls--previous', 'css');
    },
    'Test filtered job template pagination': client => {
        client
            .useCss()
            .waitForElementVisible('.SmartSearch-input')
            .clearValue('.SmartSearch-input')
            .setValue(
                '.SmartSearch-input',
                [`name.istartswith:"${namespace}"`, client.Keys.ENTER]
            );
        client.useXpath().expect.element('//a[text()="test-pagination-job-template-0"]')
            .to.be.visible.after(AWX_E2E_TIMEOUT_MEDIUM);
        client.useCss().findThenClick('.Paginate-controls--next', 'css');

        // Default search sort uses alphanumeric sorting, so template #9 is last
        client.useXpath().expect.element('//a[text()="test-pagination-job-template-9"]')
            .to.be.visible.after(AWX_E2E_TIMEOUT_MEDIUM);
        client.useXpath()
            .expect.element('//*[contains(@class, "Paginate-controls--active") and text()="2"]')
            .to.be.visible.after(AWX_E2E_TIMEOUT_MEDIUM);

        client
            .useCss()
            .findThenClick('.Paginate-controls--previous', 'css');
        // Default search sort uses alphanumeric sorting, so template #9 is last
        client.useXpath().expect.element('//a[text()="test-pagination-job-template-0"]')
            .to.be.visible.after(AWX_E2E_TIMEOUT_MEDIUM);
        client.useXpath()
            .expect.element('//*[contains(@class, "Paginate-controls--active") and text()="1"]')
            .to.be.visible.after(AWX_E2E_TIMEOUT_MEDIUM);
    },

    after: client => {
        client.end();
    }
};
