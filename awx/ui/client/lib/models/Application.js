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

function setDependentResources () {
    this.dependentResources = [];
}

function ApplicationModel (method, resource, config) {
    // TODO: change to applications
    Base.call(this, 'applications');

    this.Constructor = ApplicationModel;
    this.createFormSchema = createFormSchema.bind(this);
    this.setDependentResources = setDependentResources.bind(this);

    return this.create(method, resource, config);
}

function ApplicationModelLoader (BaseModel) {
    Base = BaseModel;

    return ApplicationModel;
}

ApplicationModelLoader.$inject = [
    'BaseModel',
];

export default ApplicationModelLoader;
