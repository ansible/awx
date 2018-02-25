import { getUpdatedProject } from '../fixtures';

const data = {};

module.exports = {
    before: (client, done) => {
        getUpdatedProject('test-actions')
            .then(obj => { data.project = obj; })
            .then(done);
    },
    'copy project': client => {
        const projects = client.page.projects();

        client.useCss();
        client.resizeWindow(1200, 800);
        client.login();
        client.waitForAngular();

        projects.navigate();
        projects.waitForElementVisible('div.spinny');
        projects.waitForElementNotVisible('div.spinny');

        projects.section.list.expect.element('smart-search').visible;
        projects.section.list.section.search.expect.element('@input').enabled;

        projects.section.list.section.search
            .sendKeys('@input', `id:>${data.project.id - 1} id:<${data.project.id + 1}`)
            .sendKeys('@input', client.Keys.ENTER);

        projects.waitForElementVisible('div.spinny');
        projects.waitForElementNotVisible('div.spinny');

        projects.section.list.expect.element('@badge').text.equal('1');
        projects.expect.element(`#projects_table tr[id="${data.project.id}"]`).visible;
        projects.expect.element('i[class*="copy"]').visible;
        projects.expect.element('i[class*="copy"]').enabled;

        projects.click('i[class*="copy"]');
        projects.waitForElementVisible('div.spinny');
        projects.waitForElementNotVisible('div.spinny');

        projects.expect.element('#project_form').visible;
        projects.section.edit.expect.element('@title').visible;
        projects.section.edit.expect.element('@title').text.contain(data.project.name);
        projects.section.edit.expect.element('@title').text.not.equal(data.project.name);
        projects.expect.element('@save').visible;
        projects.expect.element('@save').enabled;

        client.end();
    }
};
