import {
    getJob,
    getJobTemplateAdmin
} from '../fixtures';

let data;

module.exports = {
    before: (client, done) => {
        const resources = [
            getJobTemplateAdmin('test-actions'),
            getJob('test-actions'),
        ];

        Promise.all(resources)
            .then(([admin, job]) => {
                data = { admin, job };

                client.login(data.admin.username);
                client.resizeWindow(1200, 800);
                client.waitForAngular();

                done();
            });
    },
    'relaunch a job from the \'all jobs\' list': client => {
        const portal = client.page.portal();

        const allJobsButton = '#all-jobs-btn';
        const relaunch = `#job-${data.job.id} i[class*="launch"]`;
        const search = '#portal-container-jobs smart-search input';
        const spinny = 'div.spinny';

        portal.load();

        portal.expect.element(allJobsButton).visible;
        portal.expect.element(allJobsButton).enabled;
        portal.click(allJobsButton);

        portal.waitForElementVisible(spinny);
        portal.waitForElementNotVisible(spinny);

        const query = `id:>${data.job.id - 1} id:<${data.job.id + 1}`;

        portal.expect.element(search).visible;
        portal.expect.element(search).enabled;
        portal.sendKeys(search, query);
        portal.sendKeys(search, client.Keys.ENTER);

        portal.waitForElementVisible(spinny);
        portal.waitForElementNotVisible(spinny);

        portal.expect.element(relaunch).visible;
        portal.expect.element(relaunch).enabled;
        portal.click(relaunch);

        portal.waitForElementVisible(spinny);
        portal.waitForElementNotVisible(spinny);

        const jobDetails = 'at-job-details';
        const output = './/span[normalize-space(text())=\'"msg": "Hello World!"\']';

        client.waitForElementVisible(jobDetails, 10000);
        client.useXpath();
        client.waitForElementVisible(output, 60000);
        client.useCss();

        client.end();
    }
};
