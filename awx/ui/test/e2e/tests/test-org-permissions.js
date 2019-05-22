import {
    getOrganization,
    getUser,
    getTeam,
} from '../fixtures';

import {
    AWX_E2E_URL
} from '../settings';

const namespace = 'test-org-permissions';

let data;
const spinny = "//*[contains(@class, 'spinny')]";
const checkbox = '//input[@type="checkbox"]';

const searchBar = "//input[contains(@class, 'SmartSearch-input')]";
const modalSearchBar = '//*[@ui-view="modal"]//*[contains(@class, "SmartSearch-input")]';
const teamSearchBar = '//*[@django-model="teams"]//input';
const userRoleSearchBar = '//li//input[contains(@type, "search")]';
const modalOrgsSearchBar = '//smart-search[@django-model="organizations"]//input';

const orgsNavTab = "//at-side-nav-item[contains(@name, 'ORGANIZATIONS')]";
const teamsNavTab = "//at-side-nav-item[contains(@name, 'TEAMS')]";

const orgTab = '//div[not(@ng-show="showSection2Container()")]/div[@class="Form-tabHolder"]/div[@ng-click="selectTab(\'organizations\')"]';
const teamsTab = '//*[@id="teams_tab"]';
const permissionsTab = '//*[@id="permissions_tab"]';
const usersTab = '//*[@id="users_tab"]';

const orgsText = `name.iexact:"${namespace}-organization"`;
const orgsCheckbox = '//select-list-item[@item="organization"]//input[@type="checkbox"]';
const orgDetails = '//*[contains(@class, "OrgCards-label")]';
const orgRoleSelector = '//*[contains(@aria-labelledby, "select2-organizations")]';
const readRole = '//*[contains(@id, "organizations-role") and text()="Read"]';

const memberRoleText = 'member';
const readRoleText = 'read';

const teamsSelector = `//a[contains(text(), '${namespace}-team')]`;
const teamsText = `name.iexact:"${namespace}-team"`;
const teamsSearchBadgeCount = '//span[contains(@class, "List-titleBadge") and contains(text(), "1")]';
const teamCheckbox = '//*[@item="team"]//input[@type="checkbox"]';
const addUserToTeam = '//*[@aw-tool-tip="Add User"]';

const saveButton = '//*[text()="Save"]';

const addPermission = '//*[@aw-tool-tip="Grant Permission"]';
const addTeamPermission = '//*[@aw-tool-tip="Add a permission"]';
const verifyTeamPermissions = '//*[contains(@class, "List-tableRow")]//*[text()="Read"]';
const readOrgPermissionResults = `//*[@id="permissions_table"]//*[text()="${namespace}-organization"]/parent::*/parent::*//*[contains(text(), "Read")]`;

module.exports = {
    before: (client, done) => {
        const resources = [
            getUser(namespace, `${namespace}-user`),
            getOrganization(namespace),
            getTeam(namespace),
        ];

        Promise.all(resources)
            .then(([user, org, team]) => {
                data = { user, org, team };
                done();
            });
        client
            .login()
            .waitForAngular()
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
            .waitForElementVisible(modalSearchBar)
            .clearValue(modalSearchBar)
            .setValue(modalSearchBar, [`username.iexact:${data.user.username}`, client.Keys.ENTER])
            .waitForElementNotVisible(spinny)
            .findThenClick(checkbox)
            .findThenClick(userRoleSearchBar)
            .setValue(userRoleSearchBar, [memberRoleText, client.Keys.ENTER])
            .waitForElementNotVisible(spinny)
            .findThenClick(saveButton)
            // add team-wide permissions to an organization
            .findThenClick(orgsNavTab)
            .navigateTo(`${AWX_E2E_URL}/#/organizations`, false)
            .waitForElementVisible(searchBar)
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
            .findThenClick(teamCheckbox)
            .findThenClick(userRoleSearchBar)
            .setValue(userRoleSearchBar, [readRoleText, client.Keys.ENTER])
            .waitForElementNotVisible(spinny)
            .findThenClick(saveButton)
            .clearValue(searchBar)
            .setValue(searchBar, [`username.iexact:${data.user.username}`, client.Keys.ENTER])
            .waitForElementVisible(verifyTeamPermissions);
    },
    after: client => {
        client.end();
    }
};
