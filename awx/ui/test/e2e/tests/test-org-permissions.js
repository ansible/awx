import {
    getOrganization,
    getUserExact,
    getTeam,
} from '../fixtures';

let data;
const spinny = "//*[contains(@class, 'spinny')]";
const searchBar = "//input[contains(@class, 'SmartSearch-input')]";

const teamsNavTab = "//at-side-nav-item[contains(@name, 'TEAMS')]";
const teamsTab = '//*[@id="teams_tab"]';
const teamsSelector = "//a[contains(text(), 'test-actions-team')]";
const teamsText = 'name.iexact:"test-actions-team"';
const teamsSearchBadgeCount = '//span[contains(@class, "List-titleBadge") and contains(text(), "1")]';

const addUserToTeam = '//*[@aw-tool-tip="Add User"]';
const userText = 'username.iexact:"test-actions-user"';
const modalSearchBar = '//*[@ui-view="modal"]//*[contains(@class, "SmartSearch-input")]';
const checkbox = '//input[@type="checkbox"]';
const userRoleSearchBar = '//li//input[contains(@type, "search")]';
const readRoleText = "read";
const teamSearchBar = '//*[@django-model="teams"]//input';
const teamCheckbox = '//*[@item="team"]//input[@type="checkbox"]';


const permissionsTab = '//*[@id="permissions_tab"]';
const usersTab = '//*[@id="users_tab"]';
const addPermission = '//*[@aw-tool-tip="Grant Permission"]';
const addTeamPermission ='//*[@aw-tool-tip="Add a permission"]';
const orgTab = '//div[not(@ng-show="showSection2Container()")]/div[@class="Form-tabHolder"]/div[@ng-click="selectTab(\'organizations\')"]';
const modalOrgsSearchBar = '//smart-search[@django-model="organizations"]//input';
const orgsText = 'name.iexact:"test-actions-organization"';
const orgsCheckbox = '//select-list-item[@item="organization"]//input[@type="checkbox"]';
const orgDetails = '//*[contains(@class, "OrgCards-label")]';
const orgRoleSelector = '//*[contains(@aria-labelledby, "select2-organizations")]';
const readRole = '//*[contains(@id, "organizations-role") and text()="Read"]';
// const adminRole = '//*[contains(@id, "organizations-role") and text()="Admin"]';
const saveButton = '//*[text()="Save"]';

const readOrgPermissionResults = '//*[@id="permissions_table"]//*[text()="test-actions-organization"]/parent::*/parent::*//*[contains(text(), "Read")]';

const orgsNavTab = "//at-side-nav-item[contains(@name, 'ORGANIZATIONS')]";

module.exports = {
    before: (client, done) => {
        const resources = [
            getUserExact('test-actions', 'test-actions-user'),
            getOrganization('test-actions'),
            getTeam('test-actions'),
        ];

        Promise.all(resources)
            .then(([user, org, team]) => {
                data = { user, org, team };
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
    'test adding team permissions in orgs view': client => {
        // add user to team, then add team-wide permissions to org
        client
            .useXpath()
            .findThenClick(usersTab)
            .findThenClick(addUserToTeam)
            .clearValue(modalSearchBar)
            .setValue(modalSearchBar, [userText, client.Keys.ENTER])
            .waitForElementNotVisible(spinny)
            .findThenClick(checkbox)
            .findThenClick(userRoleSearchBar)
            .setValue(userRoleSearchBar, [readRoleText, client.Keys.ENTER])
            .waitForElementNotVisible(spinny)
            .findThenClick(saveButton)
            // add team-wide permissions to an organization
            .findThenClick(orgsNavTab)
            .clearValue(searchBar)
            .setValue(searchBar, [orgsText, client.Keys.ENTER])
            .waitForElementNotVisible(spinny)
            .findThenClick(orgDetails)
            .pause(3000) // overlay is in the way sometimes, not spinny
            .findThenClick(permissionsTab)
            .findThenClick(addTeamPermission)
            .findThenClick(teamsTab)
            .clearValue(teamSearchBar)
            .setValue(teamSearchBar, [teamsText, client.Keys.ENTER])
            .waitForElementNotVisible(spinny)
            .pause(4000)
            .findThenClick(teamCheckbox)
            .findThenClick(userRoleSearchBar)
            .setValue(userRoleSearchBar, [readRoleText, client.Keys.ENTER])
            .waitForElementNotVisible(spinny)
            .findThenClick(saveButton)
            .clearValue(searchBar)
            .setValue(searchBar, [userText, client.Keys.ENTER])
            .pause(4000);
    },
    after: client => {
        client.end();
    }
};
