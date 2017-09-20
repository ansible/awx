let BaseModel;

function MeModel (method, resource, graft) {
    BaseModel.call(this, 'me');

    this.Constructor = MeModel;

    return this.create(method, resource, graft)
        .then(() => {
            if (this.has('results')) {
                _.merge(this.model.GET, this.get('results[0]'));
                this.unset('results');
            }

            return this;
        });
}

function MeModelLoader (_BaseModel_) {
    BaseModel = _BaseModel_;

    return MeModel;
}

MeModelLoader.$inject = ['BaseModel'];

export default MeModelLoader;
