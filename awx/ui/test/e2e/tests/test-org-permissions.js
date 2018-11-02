import {
    getOrganization,
    getUser,
    getTeam,
} from '../fixtures';

let data;
const spinny = "//*[contains(@class, 'spinny')]";
const teamsNavTab = "//at-side-nav-item[contains(@name, 'TEAMS')]";
const teamsSelector = "//a[contains(text(), 'test-actions-team')]";
const searchBar = "//input[contains(@class, 'SmartSearch-input')]";
const teamsText = 'name.iexact:"test-actions-team"';
const teamsSearchBadgeCount = '//span[contains(@class, "List-titleBadge") and contains(text(), "1")]';

const permissionsTab = '//*[@id="permissions_tab"]';
const addPermission = '//*[@aw-tool-tip="Grant Permission"]';
const orgTab = '//div[not(@ng-show="showSection2Container()")]/div[@class="Form-tabHolder"]/div[@ng-click="selectTab(\'organizations\')"]';
const modalOrgsSearchBar = '//smart-search[@django-model="organizations"]//input';
const orgsText = 'name.iexact:"test-actions-organization"';
const orgsCheckbox = '//select-list-item[@item="organization"]//input[@type="checkbox"]';
const orgRoleSelector = '//*[contains(@aria-labelledby, "select2-organizations")]';
const readRole = '//*[contains(@id, "organizations-role") and text()="Read"]';
// const adminRole = '//*[contains(@id, "organizations-role") and text()="Admin"]';
const saveButton = '//*[text()="Save"]';

const readOrgPermissionResults = '//*[@id="permissions_table"]//*[text()="test-actions-organization"]/parent::*/parent::*//*[contains(text(), "Read")]';

module.exports = {
    before: (client, done) => {
        const resources = [
            getUser('test-actions'),
            getUser('test-actions'),
            getOrganization('test-actions'),
            getTeam('test-actions'),
        ];

        Promise.all(resources)
            .then(([user1, user2, org, team]) => {
                data = { user1, user2, org, team };
                done();
            });
        client
            .login()
            .waitForAngular()
            .resizeWindow(1200, 1000)
            .useXpath()
            .findThenClick(teamsNavTab)
            .clearValue(searchBar)
            .setValue(searchBar, [teamsText, client.Keys.ENTER])
            .waitForElementNotVisible(spinny)
            .waitForElementVisible(teamsSearchBadgeCount)
            .findThenClick(teamsSelector);
    },
    'test orgs permissions tab in teams view': client => {
        client
            .useXpath()
            .findThenClick(permissionsTab)
            .findThenClick(addPermission)
            .findThenClick(orgTab)
            .clearValue(modalOrgsSearchBar)
            .setValue(modalOrgsSearchBar, [orgsText, client.Keys.ENTER])
            .waitForElementNotVisible(spinny)
            .findThenClick(orgsCheckbox)
            .findThenClick(orgRoleSelector)
            .findThenClick(readRole)
            .findThenClick(saveButton)
            .clearValue(searchBar)
            .setValue(searchBar, [orgsText, client.Keys.ENTER])
            .waitForElementNotVisible(spinny)
            .waitForElementPresent(readOrgPermissionResults);
    },
    after: client => {
        client.end();
    }
};
