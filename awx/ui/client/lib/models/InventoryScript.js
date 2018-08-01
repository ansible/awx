let Base;
let InventorySource;

function setDependentResources (id) {
    this.dependentResources = [
        {
            model: new InventorySource(),
            params: {
                source_script: id
            }
        }
    ];
}

function createFormSchema (method, config) {
    if (!config) {
        config = method;
        method = 'GET';
    }

    const schema = Object.assign({}, this.options(`actions.${method.toUpperCase()}`));

    if (config && config.omit) {
        config.omit.forEach(key => delete schema[key]);
    }

    Object.keys(schema).forEach(key => {
        schema[key].id = key;

        if (this.has(key)) {
            schema[key]._value = this.get(key);
        }
    });

    return schema;
}

function InventoryScriptModel (method, resource, config) {
    Base.call(this, 'inventory_scripts');

    this.Constructor = InventoryScriptModel;
    this.createFormSchema = createFormSchema.bind(this);
    this.setDependentResources = setDependentResources.bind(this);

    return this.create(method, resource, config);
}

function InventoryScriptModelLoader (BaseModel, InventorySourceModel) {
    Base = BaseModel;
    InventorySource = InventorySourceModel;

    return InventoryScriptModel;
}

InventoryScriptModelLoader.$inject = [
    'BaseModel',
    'InventorySourceModel'
];

export default InventoryScriptModelLoader;
