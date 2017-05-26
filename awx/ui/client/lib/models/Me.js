function MeModel (BaseModel) {
    BaseModel.call(this, 'me');

    this.getId = () => {
        return this.model.get.data.results[0].id;
    };
}

MeModel.$inject = ['BaseModel'];

export default MeModel;
