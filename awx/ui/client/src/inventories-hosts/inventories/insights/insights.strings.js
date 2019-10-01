function InsightsStrings (BaseString) {
    BaseString.call(this, 'instanceGroups');

    const { t } = this;
    const ns = this.instanceGroups;

    ns.tooltips = {
        REFRESH_INSIGHTS: t.s('Refresh Insights'),
    };
}

InsightsStrings.$inject = ['BaseStringService'];

export default InsightsStrings;
