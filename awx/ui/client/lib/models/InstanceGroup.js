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

function InstanceGroupModel (method, resource, config) {
    // Base takes two args: resource and settings
    // resource is the string endpoint
    Base.call(this, 'instance_groups');

    this.Constructor = InstanceGroupModel;
    this.createFormSchema = createFormSchema.bind(this);

    return this.create(method, resource, config);
}

function InstanceGroupModelLoader (BaseModel) {
    Base = BaseModel;

    return InstanceGroupModel;
}

InstanceGroupModelLoader.$inject = [
    'BaseModel'
];

export default InstanceGroupModelLoader;
