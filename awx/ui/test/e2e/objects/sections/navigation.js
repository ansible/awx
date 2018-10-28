const navigation = {
    selector: 'div[class^="at-Layout-side"]',
    elements: {
        expand: 'i[class*="fa-bars"]',
        dashboard: 'i[class*="fa-tachometer"]',
        jobs: 'i[class*="fa-spinner"]',
        schedules: 'i[class*="fa-calendar"]',
        portal: 'i[class*="fa-columns"]',
        projects: 'i[class*="fa-folder-open"]',
        credentials: 'i[class*="fa-key"]',
        credentialTypes: 'i[class*="fa-list-alt"]',
        inventories: 'i[class*="fa-sitemap"]',
        templates: 'i[class*="fa-pencil-square-o"]',
        organizations: 'i[class*="fa-building"]',
        users: 'i[class*="fa-user"]',
        teams: 'i[class*="fa-users"]',
        inventoryScripts: 'i[class*="fa-code"]',
        notifications: 'i[class*="fa-bell"]',
        managementJobs: 'i[class*="fa-wrench"]',
        instanceGroups: 'i[class*="fa-server"]',
        settings: 'i[class*="fa-cog"]',
        settingsSubPane: '.at-SettingsSubPane',
        settingsSubPaneSystem: 'a[href="#/settings/system"]',
        settingsSubPaneAuth: 'a[href="#/settings/auth"]'
    }
};

module.exports = navigation;
