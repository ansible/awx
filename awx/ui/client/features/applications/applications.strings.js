function ApplicationsStrings (BaseString) {
    BaseString.call(this, 'applications');

    const { t } = this;
    const ns = this.applications;

    ns.state = {
        LIST_BREADCRUMB_LABEL: t.s('APPLICATIONS'),
        ADD_BREADCRUMB_LABEL: t.s('CREATE APPLICATION'),
        EDIT_BREADCRUMB_LABEL: t.s('EDIT APPLICATION'),
        USER_LIST_BREADCRUMB_LABEL: t.s('TOKENS')
    };

    ns.tab = {
        DETAILS: t.s('Details'),
        USERS: t.s('Tokens')
    };

    ns.tooltips = {
        ADD: t.s('Create a new Application')
    };

    ns.add = {
        PANEL_TITLE: t.s('NEW APPLICATION'),
        CLIENT_ID_LABEL: t.s('CLIENT ID'),
        CLIENT_SECRECT_LABEL: t.s('CLIENT SECRET'),
        MODAL_HEADER: t.s('APPLICATION INFORMATION'),
        NAME_LABEL: t.s('NAME'),
    };

    ns.list = {
        PANEL_TITLE: t.s('APPLICATIONS'),
        ROW_ITEM_LABEL_EXPIRED: t.s('EXPIRATION'),
        ROW_ITEM_LABEL_ORGANIZATION: t.s('ORG'),
        ROW_ITEM_LABEL_MODIFIED: t.s('LAST MODIFIED')
    };

    ns.inputs = {
        ORGANIZATION_PLACEHOLDER: t.s('SELECT AN ORGANIZATION')
    };

    ns.sort = {
        NAME_ASCENDING: t.s('Name (Ascending)'),
        NAME_DESCENDING: t.s('Name (Descending)'),
        USERNAME_ASCENDING: t.s('Username (Ascending)'),
        USERNAME_DESCENDING: t.s('Username (Descending)')
    };
}

ApplicationsStrings.$inject = ['BaseStringService'];

export default ApplicationsStrings;
