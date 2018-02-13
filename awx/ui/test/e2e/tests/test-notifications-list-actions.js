import { getNotificationTemplate } from '../fixtures';

const data = {};

module.exports = {
    before: (client, done) => {
        getNotificationTemplate('test-actions')
            .then(obj => { data.notification = obj; })
            .then(done);
    },
    'copy notification template': client => {
        const notifications = client.page.notificationTemplates();

        client.useCss();
        client.resizeWindow(1200, 800);
        client.login();
        client.waitForAngular();

        notifications.navigate();
        notifications.waitForElementVisible('div.spinny');
        notifications.waitForElementNotVisible('div.spinny');

        notifications.section.list.expect.element('smart-search').visible;
        notifications.section.list.expect.element('smart-search input').enabled;

        notifications.section.list
            .sendKeys('smart-search input', `id:>${data.notification.id - 1} id:<${data.notification.id + 1}`)
            .sendKeys('smart-search input', client.Keys.ENTER);

        notifications.waitForElementVisible('div.spinny');
        notifications.waitForElementNotVisible('div.spinny');

        notifications.expect.element(`#notification_templates_table tr[id="${data.notification.id}"]`).visible;
        notifications.expect.element('i[class*="copy"]').visible;
        notifications.expect.element('i[class*="copy"]').enabled;

        notifications.click('i[class*="copy"]');
        notifications.waitForElementVisible('div.spinny');
        notifications.waitForElementNotVisible('div.spinny');

        notifications.expect.element('#notification_template_form').visible;
        notifications.section.edit.expect.element('@title').visible;
        notifications.section.edit.expect.element('@title').text.contain(data.notification.name);
        notifications.section.edit.expect.element('@title').text.not.equal(data.notification.name);
        notifications.expect.element('@save').visible;
        notifications.expect.element('@save').enabled;

        client.end();
    }
};
