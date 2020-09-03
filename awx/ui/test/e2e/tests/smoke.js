import uuid from 'uuid';

const data = {};

const initializeData = () => {
    const id = uuid().substr(0, 8);

    data.INVENTORY_NAME = `inventory-${id}`;
    data.MACHINE_CREDENTIAL_NAME = `credential-machine-${id}`;
    data.ORGANIZATION_NAME = `organization-${id}`;
    data.PROJECT_NAME = `project-${id}`;
    data.PROJECT_URL = 'https://github.com/ansible/test-playbooks';
    data.PROJECT_BRANCH = 'devel';
    data.PLAYBOOK_NAME = 'multivault.yml';
    data.TEMPLATE_NAME = `template-${id}`;
    data.VAULT_CREDENTIAL_NAME_1 = `credential-vault-${id}-1`;
    data.VAULT_CREDENTIAL_NAME_2 = `credential-vault-${id}-2`;
};

module.exports = {
    'login to awx': client => {
        initializeData();

        client.login();
        client.waitForAngular();
    },
    'create organization': client => {
        const organizations = client.page.organizations();
        const { details } = organizations.section.add.section;

        organizations.section.navigation.waitForElementVisible('@organizations');
        organizations.section.navigation.expect.element('@organizations').enabled;
        organizations.section.navigation.click('@organizations');

        organizations.waitForElementVisible('div.spinny');
        organizations.waitForElementNotVisible('div.spinny');

        organizations.section.list.expect.element('@add').visible;
        organizations.section.list.expect.element('@add').enabled;
        organizations.section.list.click('@add');

        details.waitForElementVisible('@name');
        details.expect.element('@name').enabled;

        details.setValue('@name', data.ORGANIZATION_NAME);

        organizations.waitForElementVisible('@save');
        organizations.expect.element('@save').enabled;
        organizations.click('@save');

        organizations.waitForElementVisible('div.spinny');
        organizations.waitForElementNotVisible('div.spinny');
    },
    'create project': client => {
        const projects = client.page.projects();

        projects.section.navigation.waitForElementVisible('@projects');
        projects.section.navigation.expect.element('@projects').enabled;
        projects.section.navigation.click('@projects');

        projects.waitForElementVisible('div.spinny');
        projects.waitForElementNotVisible('div.spinny');

        projects.section.list.waitForElementVisible('@add');
        projects.section.list.expect.element('@add').enabled;

        client.pause(1000); projects.section.list.click('@add');

        projects.waitForElementVisible('label[for="name"] + div input');
        projects.waitForElementVisible('label[for="organization"] + div input');
        projects.waitForElementPresent('label[for="scm_type"] + div > div select option[value="git"]');

        projects.setValue('label[for="name"] + div input', data.PROJECT_NAME);
        projects.clearValue('label[for="organization"] + div input');
        projects.setValue('label[for="organization"] + div input', data.ORGANIZATION_NAME);
        projects.click('label[for="scm_type"] + div > div select option[value="git"]');

        projects.waitForElementVisible('.sourceSubForm');
        projects.waitForElementVisible('label[for="scm_url"] + div input');
        projects.waitForElementVisible('label[for="scm_branch"] + div input');

        projects.setValue('label[for="scm_url"] + div input', data.PROJECT_URL);
        projects.setValue('label[for="scm_branch"] + div input', data.PROJECT_BRANCH);

        projects.expect.element('#project_save_btn').enabled;
        projects.click('#project_save_btn');

        projects.waitForElementVisible('div.spinny');
        projects.waitForElementNotVisible('div.spinny');

        projects.expect.element('smart-search input').enabled;
        projects.sendKeys('smart-search input', `${data.PROJECT_NAME}${client.Keys.ENTER}`);

        projects.waitForElementVisible('div.spinny');
        projects.waitForElementNotVisible('div.spinny');

        projects.waitForElementVisible('div.spinny', 120000);
        projects.waitForElementNotVisible('div.spinny');
        projects.expect.element('i[class$="success"]').visible;

        projects.expect.element('#project_cancel_btn').visible;
        projects.click('#project_cancel_btn');
        client.refresh();
        client.waitForElementVisible('div.spinny');
        client.waitForElementNotVisible('div.spinny');
    },
    'create inventory': client => {
        const inventories = client.page.inventories();
        const details = inventories.section.addStandardInventory.section.standardInvDetails;

        inventories.section.navigation.waitForElementVisible('@inventories');
        inventories.section.navigation.expect.element('@inventories').enabled;
        inventories.section.navigation.click('@inventories');

        inventories.waitForElementVisible('div.spinny');
        inventories.waitForElementNotVisible('div.spinny');

        inventories.selectAdd('Inventory');

        details.waitForElementVisible('@name');
        details.waitForElementVisible('@organization');

        details.expect.element('@name').enabled;
        details.expect.element('@organization').enabled;

        details.setValue('@name', data.INVENTORY_NAME);
        details.setValue('@organization', data.ORGANIZATION_NAME);

        inventories.waitForElementVisible('@save');
        inventories.expect.element('@save').enabled;

        inventories.click('@save');

        inventories.waitForElementVisible('div.spinny');
        inventories.waitForElementNotVisible('div.spinny');
    },
    'create host': client => {
        const addHost = '.hostsList #button-add';

        client.expect.element('#hosts_tab').enabled;
        client.expect.element('#hosts_tab').css('opacity').equal('1');
        client.expect.element('#hosts_tab').css('background-color').contain('255, 255, 255');
        client.click('#hosts_tab');

        client.waitForElementVisible('div.spinny');
        client.waitForElementNotVisible('div.spinny');

        client.expect.element('#hosts_tab').css('background-color').contain('100, 105, 114');

        client.useCss();
        client.waitForElementVisible(addHost);
        client.expect.element(addHost).enabled;
        client.click(addHost);

        client.waitForElementVisible('#host_name');
        client.sendKeys('#host_name', 'localhost');

        client.click('div[class="CodeMirror-scroll"]');
        client.sendKeys('.CodeMirror textarea', client.Keys.ENTER);
        client.sendKeys('.CodeMirror textarea', 'ansible_connection: local');
        client.click('#host_variables_parse_type label[class$="hollow"]');
        client.click('#host_variables_parse_type label[class$="hollow"]');

        client.expect.element('#host_save_btn').enabled;
        client.click('#host_save_btn');

        client.waitForElementVisible('div.spinny');
        client.waitForElementNotVisible('div.spinny');
    },
    'create vault credentials': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;

        client.navigateTo(`${credentials.url()}/add`);

        details.waitForElementVisible('@save');
        details.clearAndSelectType('Vault');
        details.setValue('@organization', data.ORGANIZATION_NAME);
        details.setValue('@name', data.VAULT_CREDENTIAL_NAME_1);

        details.section.vault.setValue('@vaultPassword', 'secret1');
        details.section.vault.setValue('@vaultIdentifier', 'first');

        details.expect.element('@save').enabled;
        details.click('@save');

        credentials.waitForElementVisible('div.spinny');
        credentials.waitForElementNotVisible('div.spinny');

        client.navigateTo(`${credentials.url()}/add`);

        details.waitForElementVisible('@save');
        details.clearAndSelectType('Vault');
        details.setValue('@organization', data.ORGANIZATION_NAME);
        details.setValue('@name', data.VAULT_CREDENTIAL_NAME_2);

        details.section.vault.setValue('@vaultPassword', 'secret2');
        details.section.vault.setValue('@vaultIdentifier', 'second');

        details.expect.element('@save').enabled;
        details.click('@save');

        credentials.waitForElementVisible('div.spinny');
        credentials.waitForElementNotVisible('div.spinny');
    },
    'create machine credential': client => {
        const credentials = client.page.credentials();
        const { details } = credentials.section.add.section;

        client.navigateTo(`${credentials.url()}/add`);

        details.waitForElementVisible('@save');
        details.clearAndSelectType('Machine');
        details.setValue('@organization', data.ORGANIZATION_NAME);
        details.setValue('@name', data.MACHINE_CREDENTIAL_NAME);

        details.expect.element('@save').enabled;
        details.click('@save');

        credentials.waitForElementVisible('div.spinny');
        credentials.waitForElementNotVisible('div.spinny');
    },
    'create job template': client => {
        const templates = client.page.templates();

        client.navigateTo(templates.url());

        templates.selectAdd('Job Template');
        templates.selectInventory(data.INVENTORY_NAME);
        templates.selectProject(data.PROJECT_NAME);
        templates.selectVaultCredential(data.VAULT_CREDENTIAL_NAME_1);
        templates.selectVaultCredential(data.VAULT_CREDENTIAL_NAME_2);
        templates.selectMachineCredential(data.MACHINE_CREDENTIAL_NAME);
        templates.selectPlaybook(data.PLAYBOOK_NAME);
        templates.sendKeys('label[for="name"] + div input', data.TEMPLATE_NAME);

        templates.expect.element('#job_template_save_btn').enabled;
        templates.click('#job_template_save_btn');

        templates.waitForElementVisible('div.spinny');
        templates.waitForElementNotVisible('div.spinny');

        templates.expect.element('#job_template_save_btn').enabled;
    },
    'launch job': client => {
        const templates = client.page.templates();

        templates.waitForElementVisible('smart-search input');
        templates.expect.element('smart-search input').enabled;

        client.pause(1000).waitForElementNotVisible('div.spinny');
        templates.sendKeys('smart-search input', `${data.TEMPLATE_NAME}${client.Keys.ENTER}`);
        templates.waitForElementVisible('div.spinny');
        templates.waitForElementNotVisible('div.spinny');

        templates.sendKeys('smart-search input', `${data.TEMPLATE_NAME}${client.Keys.ENTER}`);
        templates.waitForElementVisible('div.spinny');
        templates.waitForElementNotVisible('div.spinny');

        templates.waitForElementPresent('i[class$="launch"]');
        templates.waitForElementNotPresent('i[class$="launch"]:nth-of-type(2)');

        templates.expect.element('.at-Panel-headingTitleBadge').text.equal('1');

        templates.waitForElementVisible('i[class$="launch"]');
        templates.click('i[class$="launch"]');
    },
    'verify expected job results': client => {
        const output1 = './/span[normalize-space(text())=\'"first": "First!"\']';
        const output2 = './/span[normalize-space(text())=\'"second": "Second!"\']';
        const running = 'i[class$="icon-job-running"]';
        const success = 'i[class$="icon-job-successful"]';

        client.waitForElementVisible('div.spinny');
        client.waitForElementNotVisible('div.spinny');

        client.waitForElementVisible('at-job-details');
        client.waitForElementNotPresent(running, 60000);
        client.waitForElementVisible(success, 60000);

        client.useXpath();
        client.waitForElementVisible(output1, 60000);
        client.waitForElementVisible(output2, 60000);
        client.useCss();

        client.end();
    }
};
