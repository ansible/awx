let BaseModel;

function getSelf () {
    return this.get('results[0]');
}

function MeModel (method, resource, graft) {
    BaseModel.call(this, 'me');

    this.Constructor = MeModel;
    this.getSelf = getSelf.bind(this);

    return this.create(method, resource, graft);
}

function MeModelLoader (_BaseModel_) {
    BaseModel = _BaseModel_;

    return MeModel;
}

MeModelLoader.$inject = ['BaseModel'];

export default MeModelLoader;
