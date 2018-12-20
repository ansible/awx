import {
    getInventorySource,
    getJobTemplate,
    getProject,
    getWorkflowTemplate,
    getJob
} from '../fixtures';

let data;
const spinny = '//*[contains(@class, "spinny")]';
const dashboard = '//at-side-nav-item[contains(@name, "DASHBOARD")]';

const sparklineIcon = '//div[contains(@class, "SmartStatus-iconContainer")]';
const running = '//div[@ng-show="job.status === \'running\'"]';

module.exports = {
    before: (client, done) => {
        const resources = [
            getInventorySource('test-websockets'),
            getJobTemplate('test-websockets'),
            getProject('test-websockets'),
            getWorkflowTemplate('test-websockets'),
        ];
        Promise.all(resources)
            .then(([inventory, job, project, workflow]) => {
                data = { inventory, job, project, workflow };
                done();
            });
        client
            .login()
            .waitForAngular()
            .resizeWindow(1200, 1000);
    },
    'Test job template status updates on dashboard': client => {
        client.useXpath().findThenClick(dashboard);
        getJob('test-websockets-job-template'); // Automatically starts job
        client.expect.element(spinny).to.not.be.visible.before(5000);
        client.expect.element(sparklineIcon + '[1]' + running)
            .to.be.visible.before(10000);
    },
    after: client => {
        client.end();
    }
};
