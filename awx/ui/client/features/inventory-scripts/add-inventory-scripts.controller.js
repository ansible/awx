function AddInventoryScriptsController (
    models,
    strings,
    $state
) {
    const vm = this || {};

    const { inventoryScript, organization } = models;

    vm.mode = 'add';
    vm.strings = strings;
    vm.panelTitle = strings.get('add.PANEL_TITLE');

    vm.tab = {
        details: { _active: true },
        users: { _disabled: true }
    };

    vm.form = inventoryScript.createFormSchema('post');

    vm.form.disabled = !inventoryScript.isCreatable();

    vm.form.organization._resource = 'organization';
    vm.form.organization._route = 'inventoryScripts.add.organization';
    vm.form.organization._model = organization;
    vm.form.organization._placeholder = strings.get('inputs.ORGANIZATION_PLACEHOLDER');

    vm.form.name.required = true;
    vm.form.organization.required = true;
    vm.form.script.required = true;

    vm.form.save = data => inventoryScript.request('post', { data });

    vm.form.onSaveSuccess = res => {
        $state.go('inventoryScripts.edit', { inventory_script_id: res.data.id }, { reload: true });
    };
}

AddInventoryScriptsController.$inject = [
    'models',
    'InventoryScriptsStrings',
    '$state'
];

export default AddInventoryScriptsController;
