let Base;

function createFormSchema (method, config) {
    function mungeSelectFromOptions (configObj, value) {
        configObj.choices = [[null, '']].concat(configObj.choices);
        configObj._data = configObj.choices;
        configObj._exp = 'choice[1] for choice in state._data';
        configObj._format = 'selectFromOptions';

        configObj._data.forEach((val, i) => {
            if (val[0] === value) {
                configObj._value = configObj._data[i];
            }
        });

        return configObj;
    }

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

        if (this.has(key) && schema[key].type !== 'choice') {
            schema[key]._value = this.get(key);
        }

        if (schema[key].type === 'choice') {
            schema[key] = mungeSelectFromOptions(schema[key], this.get(key));
        }
    });

    // necessary because authorization_grant_type is not changeable on update
    if (method === 'put') {
        schema.authorization_grant_type = mungeSelectFromOptions(Object.assign({}, this
            .options('actions.GET.authorization_grant_type')), this
            .get('authorization_grant_type'));

        schema.authorization_grant_type._required = false;
        schema.authorization_grant_type._disabled = true;
    }

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
