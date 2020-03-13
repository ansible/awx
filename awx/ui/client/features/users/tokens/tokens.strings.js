function TokensStrings (BaseString) {
    BaseString.call(this, 'tokens');

    const { t } = this;
    const ns = this.tokens;

    ns.state = {
        LIST_BREADCRUMB_LABEL: t.s('TOKENS'),
        ADD_BREADCRUMB_LABEL: t.s('CREATE TOKEN'),
        USER_LIST_BREADCRUMB_LABEL: t.s('TOKENS')
    };

    ns.tab = {
        DETAILS: t.s('Details')
    };

    ns.add = {
        PANEL_TITLE: t.s('CREATE TOKEN'),
        APP_PLACEHOLDER: t.s('SELECT AN APPLICATION'),
        SCOPE_HELP_TEXT: t.s('Specify a scope for the token\'s access'),
        TOKEN_MODAL_HEADER: t.s('TOKEN INFORMATION'),
        TOKEN_LABEL: t.s('TOKEN'),
        REFRESH_TOKEN_LABEL: t.s('REFRESH TOKEN'),
        TOKEN_EXPIRES_LABEL: t.s('EXPIRES'),
        ERROR_HEADER: t.s('COULD NOT CREATE TOKEN'),
        ERROR_BODY_LABEL: t.s('Returned status:'),
        LAST_USED_LABEL: t.s('by'),
        DELETE_ACTION_LABEL: t.s('DELETE'),
        SCOPE_PLACEHOLDER: t.s('Select a scope'),
        SCOPE_READ_LABEL: t.s('Read'),
        SCOPE_WRITE_LABEL: t.s('Write'),
        APPLICATION_HELP_TEXT: t.s('Leaving this field blank will result in the creation of a Personal Access Token which is not linked to an Application.')
    };

    ns.list = {
        ROW_ITEM_LABEL_DESCRIPTION: t.s('DESCRIPTION'),
        ROW_ITEM_LABEL_EXPIRED: t.s('EXPIRATION'),
        ROW_ITEM_LABEL_USED: t.s('LAST USED'),
        ROW_ITEM_LABEL_SCOPE: t.s('SCOPE'),
        ROW_ITEM_LABEL_APPLICATION: t.s('APPLICATION'),
        PERSONAL_ACCESS_TOKEN: t.s('Personal Access Token'),
        HEADER: appName => t.s('{{ appName }} Token', { appName }),
        ADD: t.s('Add a new token')
    };
}

TokensStrings.$inject = ['BaseStringService'];

export default TokensStrings;
