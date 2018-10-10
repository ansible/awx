function PortalModeStrings (BaseString) {
    BaseString.call(this, 'portalMode');

    const { t } = this;
    const ns = this.portalMode;

    ns.list = {
        TEMPLATES_PANEL_TITLE: t.s('JOB TEMPLATES'),
        JOBS_PANEL_TITLE: t.s('JOBS'),
    };
}

PortalModeStrings.$inject = ['BaseStringService'];

export default PortalModeStrings;
