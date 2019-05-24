import {
    getJob,
    getJobTemplateAdmin
} from '../fixtures';

let data;

module.exports = {
    before: (client, done) => {
        client.login();
        client.waitForAngular();

        const resources = [
            getJobTemplateAdmin('test-actions'),
            getJob('test-actions'),
        ];

        Promise.all(resources)
            .then(([admin, job]) => {
                data = { admin, job };
                done();
            });
    },
    'relaunch a job from the \'all jobs\' list': client => {
        const portal = client.page.portal();

        const allJobsButton = '#all-jobs-btn';
        const relaunch = `#job-${data.job.id} i[class*="launch"]`;
        const search = '#portal-container-jobs smart-search input';

        portal.load();

        portal.waitForElementVisible(allJobsButton);
        portal.expect.element(allJobsButton).enabled;
        portal.click(allJobsButton);
        portal.waitForSpinny();
        portal.assert.cssClassPresent(allJobsButton, 'btn-primary');

        const query = `id:>${data.job.id - 1} id:<${data.job.id + 1}`;

        portal.waitForElementVisible(search);
        portal.expect.element(search).enabled;
        portal.sendKeys(search, query);
        portal.sendKeys(search, client.Keys.ENTER);

        portal.waitForSpinny();

        portal.waitForElementVisible(relaunch);
        portal.expect.element(relaunch).enabled;
        portal.click(relaunch);

        portal.waitForSpinny();

        const jobDetails = 'at-job-details';
        const output = './/span[normalize-space(text())=\'"msg": "Hello World!"\']';

        client.waitForElementVisible(jobDetails, 10000);
        client.useXpath();
        client.waitForElementVisible(output, 60000);
        client.useCss();

        client.end();
    }
};
