function InsightsStrings (BaseString) {
    BaseString.call(this, 'instanceGroups');

    const { t } = this;
    const ns = this.instanceGroups;

    ns.tooltips = {
        REFRESH_INSIGHTS: t.s('Refresh Insights'),
    };

    ns.risks = {
        CRITICAL_RISK: t.s('Critical Risk'),
        HIGH_RISK: t.s('High Risk'),
        MEDIUM_RISK: t.s('Medium Risk'),
        LOW_RISK: t.s('Low Risk'),
    };
}

InsightsStrings.$inject = ['BaseStringService'];

export default InsightsStrings;
