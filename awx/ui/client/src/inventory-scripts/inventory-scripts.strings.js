function InventoryScriptsStrings (BaseString) {
    BaseString.call(this, 'inventory_scripts');

    let t = this.t;
    let ns = this.inventory_scripts;

    ns.deleteInventoryScript = {
        CONFIRM: t.s('Are you sure you want to delete this inventory script?'),
        INVALIDATE: t.s('Doing so will invalidate the following:')
    };
}

InventoryScriptsStrings.$inject = ['BaseStringService'];

export default InventoryScriptsStrings;
