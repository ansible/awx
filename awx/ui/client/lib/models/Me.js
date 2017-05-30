let BaseModel;

function MeModel (method) {
    BaseModel.call(this, 'me');

    return this.request(method)
        .then(() => this);
}

function MeModelLoader (_BaseModel_) {
    BaseModel = _BaseModel_;

    return MeModel;
}

MeModelLoader.$inject = ['BaseModel'];

export default MeModelLoader;
