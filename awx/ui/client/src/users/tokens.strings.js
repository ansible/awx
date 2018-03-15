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
        PANEL_TITLE: t.s('CREATE TOKEN')
    };

    ns.list = {
        ROW_ITEM_LABEL_EXPIRED: t.s('DESCRIPTION'),
        ROW_ITEM_LABEL_EXPIRED: t.s('EXPIRATION'),
        ROW_ITEM_LABEL_USED: t.s('LAST USED')
    };
}

TokensStrings.$inject = ['BaseStringService'];

export default TokensStrings;
