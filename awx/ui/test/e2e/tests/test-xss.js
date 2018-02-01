import {
    getAdminMachineCredential,
    getHost,
    getInventory,
    getInventoryScript,
    getInventorySource,
    getInventorySourceSchedule,
    getJobTemplate,
    getJobTemplateAdmin,
    getJobTemplateSchedule,
    getNotificationTemplate,
    getOrganization,
    getSmartInventory,
    getTeam,
    getUpdatedProject,
    getJob,
} from '../fixtures';

const data = {};
const urls = {};
const pages = {};

module.exports = {
    before: (client, done) => {
        const namespace = '<div id="xss" class="xss">test</div>';
        const namespaceShort = '<div class="xss">t</div>';

        const resources = [
            getOrganization(namespace).then(obj => { data.organization = obj; }),
            getHost(namespaceShort).then(obj => { data.host = obj; }),
            getInventory(namespace).then(obj => { data.inventory = obj; }),
            getInventoryScript(namespace).then(obj => { data.inventoryScript = obj; }),
            getSmartInventory(namespace).then(obj => { data.smartInventory = obj; }),
            getInventorySource(namespace).then(obj => { data.inventorySource = obj; }),
            getInventorySourceSchedule(namespace).then(obj => { data.sourceSchedule = obj; }),
            getUpdatedProject(namespace).then(obj => { data.project = obj; }),
            getAdminMachineCredential(namespace).then(obj => { data.credential = obj; }),
            getJobTemplate(namespace).then(obj => { data.jobTemplate = obj; }),
            getJobTemplateSchedule(namespace).then(obj => { data.jobTemplateSchedule = obj; }),
            getTeam(namespace).then(obj => { data.team = obj; }),
            getJobTemplateAdmin(namespace).then(obj => { data.user = obj; }),
            getNotificationTemplate(namespace).then(obj => { data.notification = obj; }),
            getJob(namespaceShort).then(obj => { data.job = obj; }),
        ];

        Promise.all(resources)
            .then(() => {
                pages.organizations = client.page.organizations();
                pages.inventories = client.page.inventories();
                pages.inventoryScripts = client.page.inventoryScripts();
                pages.hosts = client.page.hosts();
                pages.projects = client.page.projects();
                pages.credentials = client.page.credentials();
                pages.templates = client.page.templates();
                pages.teams = client.page.teams();
                pages.users = client.page.users();
                pages.notificationTemplates = client.page.notificationTemplates();
                pages.jobs = client.page.jobs();

                urls.organization = `${pages.organizations.url()}/${data.organization.id}`;
                urls.inventory = `${pages.inventories.url()}/inventory/${data.inventory.id}`;
                urls.hosts = `${pages.hosts.url()}`;
                urls.inventoryScript = `${pages.inventoryScripts.url()}/${data.inventoryScript.id}`;
                urls.inventorySource = `${urls.inventory}/inventory_sources/edit/${data.inventorySource.id}`;
                urls.sourceSchedule = `${urls.inventorySource}/schedules/${data.sourceSchedule.id}`;
                urls.smartInventory = `${pages.inventories.url()}/smart/${data.smartInventory.id}`;
                urls.project = `${pages.projects.url()}/${data.project.id}`;
                urls.credential = `${pages.credentials.url()}/${data.credential.id}`;
                urls.jobTemplate = `${pages.templates.url()}/job_template/${data.jobTemplate.id}`;
                urls.jobTemplateSchedule = `${urls.jobTemplate}/schedules/${data.jobTemplateSchedule.id}`;
                urls.team = `${pages.teams.url()}/${data.team.id}`;
                urls.user = `${pages.users.url()}/${data.user.id}`;
                urls.notification = `${pages.notificationTemplates.url()}/${data.notification.id}`;
                urls.jobs = `${pages.jobs.url()}`;
                urls.jobsSchedules = `${pages.jobs.url()}/schedules`;

                client.useCss();
                client.login();
                client.resizeWindow(1200, 800);
                client.waitForAngular();

                done();
            });
    },
    'check template form for unsanitized content': client => {
        const multiCredentialOpen = 'multi-credential button i[class*="search"]';
        const multiCredentialExit = 'multi-credential-modal button[class*="exit"]';

        client.url(urls.jobTemplate);

        client.expect.element('#job_template_form').visible;
        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.expect.element(multiCredentialOpen).visible;
        client.expect.element(multiCredentialOpen).enabled;

        client.pause(2000).click(multiCredentialOpen);

        client.expect.element('#multi-credential-modal').visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.click(multiCredentialExit);

        client.pause(500).expect.element('div.spinny').not.visible;
        client.expect.element('#multi-credential-modal').not.present;
    },
    'check template roles list for unsanitized content': client => {
        const itemDelete = `#permissions_table tr[id="${data.user.id}"] div[class*="RoleList-deleteContainer"]`;

        client.expect.element('#permissions_tab').visible;
        client.expect.element('#permissions_tab').enabled;

        client.click('#permissions_tab');

        client.expect.element('div.spinny').visible;
        client.expect.element('div.spinny').not.visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.expect.element('div[ui-view="related"]').visible;
        client.expect.element('div[ui-view="related"] smart-search input').enabled;

        client.sendKeys('div[ui-view="related"] smart-search input', `id:${data.user.id}`);
        client.sendKeys('div[ui-view="related"] smart-search input', client.Keys.ENTER);

        client.expect.element('div.spinny').not.visible;

        client.expect.element(itemDelete).visible;
        client.expect.element(itemDelete).enabled;

        client.click(itemDelete);

        client.expect.element('#prompt-header').visible;
        client.expect.element('#prompt-header').text.equal('USER ACCESS REMOVAL');
        client.expect.element('#prompt_cancel_btn').enabled;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.click('#prompt_cancel_btn');

        client.expect.element('#prompt-header').not.visible;
    },
    'check template permissions view for unsanitized content': client => {
        client.expect.element('button[aw-tool-tip="Add a permission"]').visible;
        client.expect.element('button[aw-tool-tip="Add a permission"]').enabled;

        client.click('button[aw-tool-tip="Add a permission"]');
        client.expect.element('div.spinny').not.visible;

        client.expect.element('div[class="AddPermissions-header"]').visible;
        client.expect.element('div[class="AddPermissions-header"]').attribute('innerHTML')
            .contains('&lt;div id="xss" class="xss"&gt;test&lt;/div&gt;');

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.expect.element('div[class="AddPermissions-dialog"] button[class*="exit"]').enabled;

        client.click('div[class="AddPermissions-dialog"] button[class*="exit"]');

        client.expect.element('div.spinny').visible;
        client.expect.element('div.spinny').not.visible;

        // client.expect.element('div.spinny').visible;
        client.expect.element('div.spinny').not.visible;
        client.waitForAngular();

        client.expect.element('#job_template_tab').enabled;

        client.click('#job_template_tab');

        client.expect.element('#job_template_form').visible;
    },
    'check template list for unsanitized content': client => {
        const itemRow = `#row-${data.jobTemplate.id}`;
        const itemName = `${itemRow} .at-RowItem-header`;

        client.expect.element('.at-Panel smart-search').visible;
        client.expect.element('.at-Panel smart-search input').enabled;

        client.sendKeys('.at-Panel smart-search input', `id:${data.jobTemplate.id}`);
        client.sendKeys('.at-Panel smart-search input', client.Keys.ENTER);

        client.expect.element('div.spinny').not.visible;

        client.expect.element('.at-Panel-headingTitleBadge').text.equal('1');
        client.expect.element(itemName).visible;

        // TODO: uncomment when tooltips are added
        // client.moveToElement(itemName, 0, 0, () => {
        //     client.expect.element(itemName).attribute('aria-describedby');
        //
        //     client.getAttribute(itemName, 'aria-describedby', ({ value }) => {
        //         const tooltip = `#${value}`;
        //
        //         client.expect.element(tooltip).present;
        //         client.expect.element(tooltip).visible;
        //
        //         client.expect.element('#xss').not.present;
        //         client.expect.element('[class=xss]').not.present;
        //         client.expect.element(tooltip).attribute('innerHTML')
        //             .contains('&lt;div id="xss" class="xss"&gt;test&lt;/div&gt;');
        //     });
        // });

        client.click(`${itemRow} i[class*="trash"]`);

        client.expect.element('#prompt-header').visible;
        client.expect.element('#prompt_cancel_btn').enabled;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.click('#prompt_cancel_btn');

        client.expect.element('#prompt-header').not.visible;
    },
    'check user form for unsanitized content': client => {
        client.navigateTo(urls.user);

        client.expect.element('#user_form').visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;
    },
    'check user roles list for unsanitized content': client => {
        const adminRole = data.jobTemplate.summary_fields.object_roles.admin_role;
        const itemDelete = `#permissions_table tr[id="${adminRole.id}"] #delete-action`;

        client.expect.element('#permissions_tab').visible;
        client.expect.element('#permissions_tab').enabled;

        client.click('#permissions_tab');

        client.expect.element('div.spinny').visible;
        client.expect.element('div.spinny').not.visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.expect.element('div[ui-view="related"]').visible;
        client.expect.element('div[ui-view="related"] smart-search input').enabled;

        client.sendKeys('div[ui-view="related"] smart-search input', `id:${adminRole.id}`);
        client.sendKeys('div[ui-view="related"] smart-search input', client.Keys.ENTER);

        client.expect.element('div.spinny').not.visible;

        client.expect.element(itemDelete).visible;
        client.expect.element(itemDelete).enabled;

        client.click(itemDelete);

        client.expect.element('#prompt-header').visible;
        client.expect.element('#prompt-header').text.equal('REMOVE ROLE');
        client.expect.element('#prompt_cancel_btn').enabled;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.click('#prompt_cancel_btn');

        client.expect.element('#prompt-header').not.visible;
    },
    'check user permissions view for unsanitized content': client => {
        client.expect.element('button[aw-tool-tip="Grant Permission"]').enabled;

        client.click('button[aw-tool-tip="Grant Permission"]');

        client.expect.element('div.spinny').visible;
        client.expect.element('div.spinny').not.visible;
        client.expect.element('div[class="AddPermissions-header"]').visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.expect.element('div[class="AddPermissions-dialog"] button[class*="exit"]').enabled;

        client.click('div[class="AddPermissions-dialog"] button[class*="exit"]');

        client.expect.element('div.spinny').visible;
        client.expect.element('div.spinny').not.visible;
    },
    'check notification form for unsanitized content': client => {
        client.navigateTo(urls.notification);

        client.expect.element('#notification_template_form').visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;
    },
    'check notification list for unsanitized content': client => {
        const itemRow = `#notification_templates_table tr[id="${data.notification.id}"]`;
        const itemName = `${itemRow} td[class*="name-"] a`;

        client.expect.element('div[class^="Panel"] smart-search').visible;
        client.expect.element('div[class^="Panel"] smart-search input').enabled;

        client.sendKeys('div[class^="Panel"] smart-search input', `id:${data.notification.id}`);
        client.sendKeys('div[class^="Panel"] smart-search input', client.Keys.ENTER);

        client.expect.element('div.spinny').visible;
        client.expect.element('div.spinny').not.visible;

        client.expect.element('.List-titleBadge').text.equal('1');
        client.expect.element(itemName).visible;

        client.moveToElement(itemName, 0, 0, () => {
            client.expect.element(itemName).attribute('aria-describedby');

            client.getAttribute(itemName, 'aria-describedby', ({ value }) => {
                const tooltip = `#${value}`;

                client.expect.element(tooltip).present;
                client.expect.element(tooltip).visible;

                client.expect.element('#xss').not.present;
                client.expect.element('[class=xss]').not.present;
                client.expect.element(tooltip).attribute('innerHTML')
                    .contains('&lt;div id="xss" class="xss"&gt;test&lt;/div&gt;');
            });
        });

        client.click(`${itemRow} i[class*="trash"]`);

        client.expect.element('#prompt-header').visible;
        client.expect.element('#prompt_cancel_btn').enabled;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.click('#prompt_cancel_btn');

        client.expect.element('#prompt-header').not.visible;
    },
    'check organization form for unsanitized content': client => {
        client.navigateTo(urls.organization);

        client.expect.element('#organization_form').visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;
    },
    'check organization list for unsanitized content': client => {
        const itemName = '#OrgCards h3[class*="-label"]';

        client.expect.element('div[class^="Panel"] smart-search').visible;
        client.expect.element('div[class^="Panel"] smart-search input').enabled;

        client.sendKeys('div[class^="Panel"] smart-search input', `id:${data.organization.id}`);
        client.sendKeys('div[class^="Panel"] smart-search input', client.Keys.ENTER);

        client.expect.element('div.spinny').visible;
        client.expect.element('div.spinny').not.visible;

        client.expect.element(itemName).visible;

        client.moveToElement(itemName, 0, 0, () => {
            client.expect.element(itemName).attribute('aria-describedby');

            client.getAttribute(itemName, 'aria-describedby', ({ value }) => {
                const tooltip = `#${value}`;

                client.expect.element(tooltip).present;
                client.expect.element(tooltip).visible;

                client.expect.element('#xss').not.present;
                client.expect.element('[class=xss]').not.present;
                client.expect.element(tooltip).attribute('innerHTML')
                    .contains('&lt;div id="xss" class="xss"&gt;test&lt;/div&gt;');
            });
        });

        client.click('#OrgCards i[class*="trash"]');

        client.expect.element('#prompt-header').visible;
        client.expect.element('#prompt_cancel_btn').enabled;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.click('#prompt_cancel_btn');

        client.expect.element('#prompt-header').not.visible;
    },
    'check inventory form for unsanitized content': client => {
        client.navigateTo(urls.inventory);

        client.expect.element('#inventory_form').visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;
    },
    'check inventory list for unsanitized content': client => {
        const itemRow = `#inventories_table tr[id="${data.inventory.id}"]`;
        const itemName = `${itemRow} td[class*="name-"] a`;

        client.expect.element('div[class^="Panel"] smart-search').visible;
        client.expect.element('div[class^="Panel"] smart-search input').enabled;

        client.sendKeys('div[class^="Panel"] smart-search input', `id:${data.inventory.id}`);
        client.sendKeys('div[class^="Panel"] smart-search input', client.Keys.ENTER);

        client.expect.element('div.spinny').visible;
        client.expect.element('div.spinny').not.visible;

        // client.expect.element('.List-titleBadge').text.equal('1');
        client.expect.element(itemName).visible;

        client.moveToElement(itemName, 0, 0, () => {
            client.expect.element(itemName).attribute('aria-describedby');

            client.getAttribute(itemName, 'aria-describedby', ({ value }) => {
                const tooltip = `#${value}`;

                client.expect.element(tooltip).present;
                client.expect.element(tooltip).visible;

                client.expect.element('#xss').not.present;
                client.expect.element('[class=xss]').not.present;
                client.expect.element(tooltip).attribute('innerHTML')
                    .contains('&lt;div id="xss" class="xss"&gt;test&lt;/div&gt;');
            });
        });

        client.click(`${itemRow} i[class*="trash"]`);

        client.expect.element('#prompt-header').visible;
        client.expect.element('#prompt_cancel_btn').enabled;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.click('#prompt_cancel_btn');

        client.expect.element('#prompt-header').not.visible;
    },
    'check smart inventory form for unsanitized content': client => {
        client.url(urls.smartInventory);

        client.expect.element('#smartinventory_form').visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;
    },
    'check inventory script form for unsanitized content': client => {
        client.navigateTo(urls.inventoryScript);

        client.expect.element('#inventory_script_form').visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;
    },
    'check inventory script list for unsanitized content': client => {
        const itemRow = `#inventory_scripts_table tr[id="${data.inventoryScript.id}"]`;
        const itemName = `${itemRow} td[class*="name-"] a`;

        client.expect.element('div[class^="Panel"] smart-search').visible;
        client.expect.element('div[class^="Panel"] smart-search input').enabled;

        client.sendKeys('div[class^="Panel"] smart-search input', `id:${data.inventoryScript.id}`);
        client.sendKeys('div[class^="Panel"] smart-search input', client.Keys.ENTER);

        client.expect.element('div.spinny').visible;
        client.expect.element('div.spinny').not.visible;

        client.expect.element('.List-titleBadge').text.equal('1');
        client.expect.element(itemName).visible;

        client.moveToElement(itemName, 0, 0, () => {
            client.expect.element(itemName).attribute('aria-describedby');

            client.getAttribute(itemName, 'aria-describedby', ({ value }) => {
                const tooltip = `#${value}`;

                client.expect.element(tooltip).present;
                client.expect.element(tooltip).visible;

                client.expect.element('#xss').not.present;
                client.expect.element('[class=xss]').not.present;
                client.expect.element(tooltip).attribute('innerHTML')
                    .contains('&lt;div id="xss" class="xss"&gt;test&lt;/div&gt;');
            });
        });

        client.click(`${itemRow} i[class*="trash"]`);

        client.expect.element('#prompt-header').visible;
        client.expect.element('#prompt_cancel_btn').enabled;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.click('#prompt_cancel_btn');

        client.expect.element('#prompt-header').not.visible;
    },
    'check project form for unsanitized content': client => {
        client.navigateTo(urls.project);

        client.expect.element('#project_form').visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;
    },
    'check project list for unsanitized content': client => {
        const itemRow = `#projects_table tr[id="${data.project.id}"]`;
        const itemName = `${itemRow} td[class*="name-"] a`;

        client.expect.element('div[class^="Panel"] smart-search').visible;
        client.expect.element('div[class^="Panel"] smart-search input').enabled;

        client.sendKeys('div[class^="Panel"] smart-search input', `id:${data.project.id}`);
        client.sendKeys('div[class^="Panel"] smart-search input', client.Keys.ENTER);

        client.expect.element('div.spinny').visible;
        client.expect.element('div.spinny').not.visible;

        client.expect.element('.List-titleBadge').text.equal('1');
        client.expect.element(itemName).visible;

        client.moveToElement(itemName, 0, 0, () => {
            client.expect.element(itemName).attribute('aria-describedby');

            client.getAttribute(itemName, 'aria-describedby', ({ value }) => {
                const tooltip = `#${value}`;

                client.expect.element(tooltip).present;
                client.expect.element(tooltip).visible;

                client.expect.element('#xss').not.present;
                client.expect.element('[class=xss]').not.present;
                client.expect.element(tooltip).attribute('innerHTML')
                    .contains('&lt;div id="xss" class="xss"&gt;test&lt;/div&gt;');
            });
        });

        client.click(`${itemRow} i[class*="trash"]`);

        client.expect.element('#prompt-header').visible;
        client.expect.element('#prompt_cancel_btn').enabled;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.click('#prompt_cancel_btn');

        client.expect.element('#prompt-header').not.visible;
    },
    'check credential form for unsanitized content': client => {
        client.navigateTo(urls.credential);

        client.expect.element('div[ui-view="edit"] form').visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;
    },
    'check credential list for unsanitized content': client => {
        const itemRow = `#credentials_table tr[id="${data.credential.id}"]`;
        const itemName = `${itemRow} td[class*="name-"] a`;

        client.expect.element('div[ui-view="list"] smart-search').visible;
        client.expect.element('div[ui-view="list"] smart-search input').enabled;

        client.sendKeys('div[ui-view="list"] smart-search input', `id:${data.credential.id}`);
        client.sendKeys('div[ui-view="list"] smart-search input', client.Keys.ENTER);

        client.expect.element('div.spinny').visible;
        client.expect.element('div.spinny').not.visible;

        client.expect.element('.List-titleBadge').text.equal('1');
        client.expect.element(itemName).visible;

        client.moveToElement(itemName, 0, 0, () => {
            client.expect.element(itemName).attribute('aria-describedby');

            client.getAttribute(itemName, 'aria-describedby', ({ value }) => {
                const tooltip = `#${value}`;

                client.expect.element(tooltip).present;
                client.expect.element(tooltip).visible;

                client.expect.element('#xss').not.present;
                client.expect.element('[class=xss]').not.present;
                client.expect.element(tooltip).attribute('innerHTML')
                    .contains('&lt;div id="xss" class="xss"&gt;test&lt;/div&gt;');
            });
        });

        client.click(`${itemRow} i[class*="trash"]`);

        client.expect.element('#prompt-header').visible;
        client.expect.element('#prompt_cancel_btn').enabled;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.click('#prompt_cancel_btn');

        client.expect.element('#prompt-header').not.visible;
    },
    'check team form for unsanitized content': client => {
        client.navigateTo(urls.team);

        client.expect.element('#team_form').visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;
    },
    'check team list for unsanitized content': client => {
        const itemRow = `#teams_table tr[id="${data.team.id}"]`;
        const itemName = `${itemRow} td[class*="name-"] a`;

        client.expect.element('div[class^="Panel"] smart-search').visible;
        client.expect.element('div[class^="Panel"] smart-search input').enabled;

        client.sendKeys('div[class^="Panel"] smart-search input', `id:${data.team.id}`);
        client.sendKeys('div[class^="Panel"] smart-search input', client.Keys.ENTER);

        client.expect.element('div.spinny').visible;
        client.expect.element('div.spinny').not.visible;

        client.expect.element('.List-titleBadge').text.equal('1');
        client.expect.element(itemName).visible;

        client.moveToElement(itemName, 0, 0, () => {
            client.expect.element(itemName).attribute('aria-describedby');

            client.getAttribute(itemName, 'aria-describedby', ({ value }) => {
                const tooltip = `#${value}`;

                client.expect.element(tooltip).present;
                client.expect.element(tooltip).visible;

                client.expect.element('#xss').not.present;
                client.expect.element('[class=xss]').not.present;
                client.expect.element(tooltip).attribute('innerHTML')
                    .contains('&lt;div id="xss" class="xss"&gt;test&lt;/div&gt;');
            });
        });

        client.click(`${itemRow} i[class*="trash"]`);

        client.expect.element('#prompt-header').visible;
        client.expect.element('#prompt_cancel_btn').enabled;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.click('#prompt_cancel_btn');

        client.expect.element('#prompt-header').not.visible;
    },
    'check inventory source schedule view for unsanitized content': client => {
        client.navigateTo(urls.sourceSchedule);
        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;
    },
    'check job template schedule view for unsanitized content': client => {
        client.navigateTo(urls.jobTemplateSchedule);
        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;
    },
    'check job schedules view for unsanitized content': client => {
        const itemRow = `#schedules_table tr[id="${data.jobTemplateSchedule.id}"]`;
        const itemName = `${itemRow} td[class*="name-"] a`;

        client.navigateTo(urls.jobsSchedules);

        client.moveToElement(itemName, 0, 0, () => {
            client.expect.element(itemName).attribute('aria-describedby');
            client.getAttribute(itemName, 'aria-describedby', ({ value }) => {
                const tooltip = `#${value}`;
                client.expect.element(tooltip).present;
                client.expect.element(tooltip).visible;

                client.expect.element('#xss').not.present;
                client.expect.element('[class=xss]').not.present;
                client.expect.element(tooltip).attribute('innerHTML')
                    .contains('&lt;div id="xss" class="xss"&gt;test&lt;/div&gt;');
            });
        });
        client.end();
    },
    'check host recent jobs popup for unsanitized content': client => {
        const itemRow = `#hosts_table tr[id="${data.host.id}"]`;
        const itemName = `${itemRow} td[class*="active_failures-"] a`;
        const popOver = `${itemRow} td[class*="active_failures-"] div[class*="popover"]`;

        client.navigateTo(urls.hosts);

        client.click(itemName);
        client.expect.element(popOver).present;

        client.expect.element('[class=xss]').not.present;

        client.end();
    },
};
