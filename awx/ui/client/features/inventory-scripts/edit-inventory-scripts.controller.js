function EditInventoryScriptsController (
    models,
    strings,
    $state
) {
    const vm = this || {};

    const { inventoryScript, organization } = models;

    const isEditable = inventoryScript.isEditable();

    vm.mode = 'edit';
    vm.strings = strings;
    vm.panelTitle = inventoryScript.get('name');
    vm.name = inventoryScript.get('name');

    if (isEditable) {
        vm.form = inventoryScript.createFormSchema('put');
    } else {
        vm.form = inventoryScript.createFormSchema();
    }

    vm.form.disabled = !isEditable;

    vm.form.name.required = true;
    vm.form.organization.required = true;
    vm.form.script.required = true;

    vm.form.organization._resource = 'organization';
    vm.form.organization._model = organization;
    vm.form.organization._route = 'inventoryScripts.edit.organization';
    vm.form.organization._value = inventoryScript.get('summary_fields.organization.id');
    vm.form.organization._displayValue = inventoryScript.get('summary_fields.organization.name');
    vm.form.organization._placeholder = strings.get('inputs.ORGANIZATION_PLACEHOLDER');
    vm.form.organization.required = true;

    vm.form.save = data => inventoryScript.request('put', { data });

    vm.form.onSaveSuccess = () => {
        $state.go('.', null, { reload: true });
    };
}

EditInventoryScriptsController.$inject = [
    'models',
    'InventoryScriptsStrings',
    '$state'
];

export default EditInventoryScriptsController;
