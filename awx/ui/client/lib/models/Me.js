let BaseModel;

function getSelf () {
    return this.get('results[0]');
}

function MeModel (method) {
    BaseModel.call(this, 'me');

    this.getSelf = getSelf.bind(this);

    return this.request(method)
        .then(() => this);
}

function MeModelLoader (_BaseModel_) {
    BaseModel = _BaseModel_;

    return MeModel;
}

MeModelLoader.$inject = ['BaseModel'];

export default MeModelLoader;
