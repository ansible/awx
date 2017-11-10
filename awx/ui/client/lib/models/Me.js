let Base;

function MeModel (method, resource, config) {
    Base.call(this, 'me');

    this.Constructor = MeModel;

    return this.create(method, resource, config)
        .then(() => {
            if (this.has('results')) {
                _.merge(this.model.GET, this.get('results[0]'));
                this.unset('results');
            }

            return this;
        });
}

function MeModelLoader (BaseModel) {
    Base = BaseModel;

    return MeModel;
}

MeModelLoader.$inject = ['BaseModel'];

export default MeModelLoader;
