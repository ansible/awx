let BaseModel;

function InventoryUpdateModel (method, resource, config) {
    BaseModel.call(this, 'inventory_updates');

    this.Constructor = InventoryUpdateModel;

    return this.create(method, resource, config);
}

function InventoryUpdateModelLoader (_BaseModel_) {
    BaseModel = _BaseModel_;

    return InventoryUpdateModel;
}

InventoryUpdateModelLoader.$inject = [
    'BaseModel'
];

export default InventoryUpdateModelLoader;
