let Base;

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

function InstanceModel (method, resource, config) {
    // Base takes two args: resource and settings
    // resource is the string endpoint
    Base.call(this, 'instances');

    this.Constructor = InstanceModel;
    this.createFormSchema = createFormSchema.bind(this);

    return this.create(method, resource, config);
}

function InstanceModelLoader (BaseModel) {
    Base = BaseModel;

    return InstanceModel;
}

InstanceModelLoader.$inject = [
    'BaseModel'
];

export default InstanceModelLoader;
