import {
    getAdminMachineCredential,
    getHost,
    getInventory,
    getInventoryScript,
    getInventorySource,
    getInventorySourceSchedule,
    getJobTemplate,
    getJobTemplateSchedule,
    getNotificationTemplate,
    getOrganization,
    getProjectAdmin,
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
            getProjectAdmin(namespace).then(obj => { data.user = obj; }),
            getNotificationTemplate(namespace).then(obj => { data.notification = obj; }),
            getJob(namespace).then(obj => { data.job = obj; }),
        ];

        Promise.all(resources)
            .then(() => {
                pages.organizations = client.page.organizations();
                pages.inventories = client.page.inventories();
                pages.inventoryScripts = client.page.inventoryScripts();
                pages.projects = client.page.projects();
                pages.credentials = client.page.credentials();
                pages.templates = client.page.templates();
                pages.teams = client.page.teams();
                pages.users = client.page.users();
                pages.notificationTemplates = client.page.notificationTemplates();
                pages.jobs = client.page.jobs();

                urls.organization = `${pages.organizations.url()}/${data.organization.id}`;
                urls.inventory = `${pages.inventories.url()}/inventory/${data.inventory.id}`;
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
                urls.inventoryHosts = `${pages.inventories.url()}/inventory/${data.host.summary_fields.inventory.id}/hosts`;

                client
                    .useCss()
                    .login()
                    .waitForAngular()
                    .resizeWindow(1200, 800);

                done();
            });
    },
    'check template form for unsanitized content': client => {
        const multiCredentialOpen = 'multi-credential button i[class*="search"]';

        client.navigateTo(urls.jobTemplate, false);

        client.expect.element('#job_template_form').visible;
        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.expect.element(multiCredentialOpen).visible;
        client.expect.element(multiCredentialOpen).enabled;

        client.pause(2000).click(multiCredentialOpen);

        client.expect.element('#multi-credential-modal').visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.pause(500);

        client.waitForElementVisible('#multi-credential-modal .Form-exit');
        client.waitForElementNotVisible('.overlay');

        client.click('#multi-credential-modal .Form-exit');

        client.waitForElementNotPresent('#multi-credential-modal');
    },
    'check template list for unsanitized content': client => {
        const itemRow = `#row-${data.jobTemplate.id}`;
        const itemName = `${itemRow} .at-RowItem-header`;

        client.expect.element('.at-Panel smart-search').visible;
        client.expect.element('.at-Panel smart-search input').enabled;

        client.sendKeys('.at-Panel smart-search input', `id:>${data.jobTemplate.id - 1} id:<${data.jobTemplate.id + 1}`);
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
        if (client.isVisible('#prompt_cancel_btn')) {
            client.click('#prompt_cancel_btn');
        }

        client.expect.element('#prompt-header').not.visible;
    },
    'check user form for unsanitized content': client => {
        client.navigateTo(urls.user);

        client.expect.element('#user_form').visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;
    },
    // This test is disabled, because we don't have access to the permission
    // id to craft the correct ID selector
    // 'check user roles list for unsanitized content': client => {
    //     const adminRole = data.project.summary_fields.object_roles.admin_role;
    //     const itemDelete = `#permissions_table .List-tableRow[id="${adminRole.id}"]
    //     #permission-${"TODO: NEED ROLE ID, don't have fixture to get it"}-delete-action`;

    //     client.expect.element('#permissions_tab').visible;
    //     client.expect.element('#permissions_tab').enabled;

    //     client.pause(2000);
    //     client.findThenClick('#permissions_tab', 'css');

    //     client.expect.element('#xss').not.present;
    //     client.expect.element('[class=xss]').not.present;

    //     client.expect.element('div[ui-view="related"]').visible;
    //     client.expect.element('div[ui-view="related"] smart-search input').enabled;

    //     client.sendKeys('div[ui-view="related"] smart-search input',
    //     `id:>${adminRole.id - 1} id:<${adminRole.id + 1}`);
    //     client.sendKeys('div[ui-view="related"] smart-search input', client.Keys.ENTER);

    //     client.expect.element('div.spinny').not.visible;

    //     client.expect.element(itemDelete).visible;
    //     client.expect.element(itemDelete).enabled;

    //     client.click(itemDelete);

    //     client.expect.element('#prompt-header').visible;
    //     client.expect.element('#prompt-header').text.equal('REMOVE ROLE');
    //     client.expect.element('#prompt_cancel_btn').enabled;

    //     client.expect.element('#xss').not.present;
    //     client.expect.element('[class=xss]').not.present;

    //     client.click('#prompt_cancel_btn');

    //     client.expect.element('#prompt-header').not.visible;
    // },
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
        const itemRow = `#notification_templates_table .List-tableRow[id="${data.notification.id}"]`;
        const itemName = `${itemRow} .List-tableCell[class*="name-"] a`;

        client.expect.element('div.at-Panel smart-search').visible;
        client.expect.element('div.at-Panel smart-search input').enabled;

        client.sendKeys('div.at-Panel smart-search input', `id:>${data.notification.id - 1} id:<${data.notification.id + 1}`);
        client.waitForElementNotPresent('div.at-Panel smart-search .SmartSearch-searchButton--disabled');
        client.waitForElementNotVisible('.overlay');
        client.pause(2000);
        client.click('div.at-Panel smart-search .SmartSearch-searchButton');

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
        if (client.isVisible('#prompt_cancel_btn')) {
            client.click('#prompt_cancel_btn');
        }

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

        client.expect.element('div.at-Panel smart-search').visible;
        client.expect.element('div.at-Panel smart-search input').enabled;

        client.sendKeys('div.at-Panel smart-search input', `id:>${data.organization.id - 1} id:<${data.organization.id + 1}`);
        client.waitForElementNotPresent('div.at-Panel smart-search .SmartSearch-searchButton--disabled');
        client.waitForElementNotVisible('.overlay');
        client.click('div.at-Panel smart-search .SmartSearch-searchButton');

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
        if (client.isVisible('#prompt_cancel_btn')) {
            client.click('#prompt_cancel_btn');
        }

        client.expect.element('#prompt-header').not.visible;
    },
    'check inventory form for unsanitized content': client => {
        client.navigateTo(urls.inventory);

        client.expect.element('#inventory_form').visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;
    },
    'check inventory list for unsanitized content': client => {
        const itemRow = `#inventories_table .List-tableRow[id="${data.inventory.id}"]`;
        const itemName = `${itemRow} .List-tableCell[class*="name-"] a`;

        client.expect.element('div.at-Panel smart-search').visible;
        client.expect.element('div.at-Panel smart-search input').enabled;

        client.sendKeys('div.at-Panel smart-search input', `id:>${data.inventory.id - 1} id:<${data.inventory.id + 1}`);
        client.waitForElementNotPresent('div.at-Panel smart-search .SmartSearch-searchButton--disabled');
        client.waitForElementNotVisible('.overlay');
        client.click('div.at-Panel smart-search .SmartSearch-searchButton');

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
        if (client.isVisible('#prompt_cancel_btn')) {
            client.click('#prompt_cancel_btn');
        }

        client.expect.element('#prompt-header').not.visible;
    },
    'check smart inventory form for unsanitized content': client => {
        client.navigateTo(urls.smartInventory, false);

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
        const itemRow = `#inventory_scripts_table .List-tableRow[id="${data.inventoryScript.id}"]`;
        const itemName = `${itemRow} .List-tableCell[class*="name-"] a`;

        client.expect.element('div.at-Panel smart-search').visible;
        client.expect.element('div.at-Panel smart-search input').enabled;

        client.sendKeys('div.at-Panel smart-search input', `id:>${data.inventoryScript.id - 1} id:<${data.inventoryScript.id + 1}`);
        client.waitForElementNotPresent('div.at-Panel smart-search .SmartSearch-searchButton--disabled');
        client.waitForElementNotVisible('.overlay');
        client.click('div.at-Panel smart-search .SmartSearch-searchButton');

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
        if (client.isVisible('#prompt_cancel_btn')) {
            client.click('#prompt_cancel_btn');
        }

        client.expect.element('#prompt-header').not.visible;
    },
    'check project form for unsanitized content': client => {
        client.navigateTo(urls.project);

        client.expect.element('#project_form').visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;
    },
    'check project roles list for unsanitized content': client => {
        const itemDelete = `#permissions_table .List-tableRow[id="${data.user.id}"] div[class*="RoleList-deleteContainer"]`;

        client.expect.element('#permissions_tab').visible;
        client.expect.element('#permissions_tab').enabled;

        client.pause(1000);
        client.click('#permissions_tab');
        client.click('#permissions_tab');

        client.expect.element('div.spinny').visible;
        client.expect.element('div.spinny').not.visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;

        client.expect.element('div[ui-view="related"]').visible;
        client.expect.element('div[ui-view="related"] smart-search input').enabled;

        client.sendKeys('div[ui-view="related"] smart-search input', `id:>${data.user.id - 1} id:<${data.user.id + 1}`);
        client.waitForElementNotPresent('div[ui-view="related"] smart-search .SmartSearch-searchButton--disabled');
        client.waitForElementNotVisible('.overlay');
        client.click('div[ui-view="related"] smart-search .SmartSearch-searchButton');

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
    'check project permissions view for unsanitized content': client => {
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

        client.expect.element('#project_tab').enabled;

        client.click('#project_tab');

        client.expect.element('#project_form').visible;
    },
    'check project list for unsanitized content': client => {
        const itemRow = `#row-${data.project.id}`;
        const itemName = `${itemRow} .at-RowItem-header`;

        client.expect.element('.at-Panel smart-search').visible;
        client.expect.element('.at-Panel smart-search input').enabled;

        client.sendKeys('.at-Panel smart-search input', `id:>${data.project.id - 1} id:<${data.project.id + 1}`);
        client.waitForElementNotPresent('div.at-Panel smart-search .SmartSearch-searchButton--disabled');
        client.waitForElementNotVisible('.overlay');
        client.click('div.at-Panel smart-search .SmartSearch-searchButton');

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
        if (client.isVisible('#prompt_cancel_btn')) {
            client.click('#prompt_cancel_btn');
        }

        client.expect.element('#prompt-header').not.visible;
    },
    'check credential form for unsanitized content': client => {
        client.navigateTo(urls.credential);

        client.expect.element('div[ui-view="edit"] form').visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;
    },
    'check credential list for unsanitized content': client => {
        const itemRow = `#credentials_table .List-tableRow[id="${data.credential.id}"]`;
        const itemName = `${itemRow} .List-tableCell[class*="name-"] a`;

        client.expect.element('div[ui-view="list"] smart-search').visible;
        client.expect.element('div[ui-view="list"] smart-search input').enabled;

        client.sendKeys('div[ui-view="list"] smart-search input', `id:>${data.credential.id - 1} id:<${data.credential.id + 1}`);
        client.waitForElementNotPresent('div[ui-view="list"] smart-search .SmartSearch-searchButton--disabled');
        client.waitForElementNotVisible('.overlay');
        client.click('div[ui-view="list"] smart-search .SmartSearch-searchButton');

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
        if (client.isVisible('#prompt_cancel_btn')) {
            client.click('#prompt_cancel_btn');
        }

        client.expect.element('#prompt-header').not.visible;
    },
    'check team form for unsanitized content': client => {
        client.navigateTo(urls.team);

        client.expect.element('#team_form').visible;

        client.expect.element('#xss').not.present;
        client.expect.element('[class=xss]').not.present;
    },
    'check team list for unsanitized content': client => {
        const itemRow = `#teams_table .List-tableRow[id="${data.team.id}"]`;
        const itemName = `${itemRow} .List-tableCell[class*="name-"] a`;

        client.expect.element('div.at-Panel smart-search').visible;
        client.expect.element('div.at-Panel smart-search input').enabled;

        client.sendKeys('div.at-Panel smart-search input', `id:>${data.team.id - 1} id:<${data.team.id + 1}`);
        client.waitForElementNotPresent('div.at-Panel smart-search .SmartSearch-searchButton--disabled');
        client.waitForElementNotVisible('.overlay');
        client.click('div.at-Panel smart-search .SmartSearch-searchButton');

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
        if (client.isVisible('#prompt_cancel_btn')) {
            client.click('#prompt_cancel_btn');
        }

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
        const itemRow = `#schedules_table .List-tableRow[id="${data.jobTemplateSchedule.id}"]`;
        const itemName = `${itemRow} .List-tableCell[class*="name-"] a`;

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
    },
    'check host recent jobs popup for unsanitized content': client => {
        const itemRow = `#hosts_table .List-tableRow[id="${data.host.id}"]`;
        const itemName = `${itemRow} .List-tableCell[class*="active_failures-"] a`;

        client.navigateTo(urls.inventoryHosts);
        client.expect.element('div.at-Panel smart-search').visible;
        client.expect.element('div.at-Panel smart-search input').enabled;

        client.sendKeys('div[ui-view="form"] smart-search input', `id:>${data.host.id - 1} id:<${data.host.id + 1}`);
        client.waitForElementNotPresent('div[ui-view="form"] smart-search .SmartSearch-searchButton--disabled');
        client.waitForElementNotVisible('.overlay');
        client.click('div[ui-view="form"] smart-search .SmartSearch-searchButton');

        client.expect.element('div.spinny').visible;
        client.expect.element('div.spinny').not.visible;

        client.click(itemName);
        client.expect.element('body > div.popover').present;

        client.expect.element('[class=xss]').not.present;

        client.end();
    },
};
