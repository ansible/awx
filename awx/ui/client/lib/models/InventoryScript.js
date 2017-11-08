let BaseModel;
let InventorySourceModel;
let ModelsStrings;

function setDependentResources (id) {
    this.dependentResources = [
        {
            model: new InventorySourceModel(),
            params: {
                source_script: id
            }
        }
    ];
}

function InventoryScriptModel (method, resource, graft) {
    BaseModel.call(this, 'inventory_scripts');

    this.Constructor = InventoryScriptModel;
    this.setDependentResources = setDependentResources.bind(this);
    this.label = ModelsStrings.get('labels.INVENTORY_SCRIPT');

    return this.create(method, resource, graft);
}

function InventoryScriptModelLoader (
    _BaseModel_,
    _InventorySourceModel_,
    _ModelsStrings_
) {
    BaseModel = _BaseModel_;
    InventorySourceModel = _InventorySourceModel_;
    ModelsStrings = _ModelsStrings_;

    return InventoryScriptModel;
}

InventoryScriptModelLoader.$inject = [
    'BaseModel',
    'InventorySourceModel',
    'ModelsStrings'
];

export default InventoryScriptModelLoader;
