function InventoryScriptsStrings (BaseString) {
    BaseString.call(this, 'inventory_scripts');

    let t = this.t;
    let ns = this.inventory_scripts;

    ns.deleteInventoryScript = {
        CONFIRM: t.s('The inventory script is currently being used by other resources. Are you sure you want to delete this inventory script?')
    };
}

InventoryScriptsStrings.$inject = ['BaseStringService'];

export default InventoryScriptsStrings;
