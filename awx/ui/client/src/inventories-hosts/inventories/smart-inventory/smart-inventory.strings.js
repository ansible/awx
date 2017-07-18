function SmartInventoryStrings (BaseString) {
    BaseString.call(this, 'smartinventories');

    let t = this.t;
    let ns = this.smartinventories;

    ns.filter = {
        TOOLTIP: t('Please click the icon to edit the host filter.')
    };
}

SmartInventoryStrings.$inject = ['BaseStringService'];

export default SmartInventoryStrings;
