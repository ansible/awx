let BaseModel;

function ProjectUpdateModel (method, resource, config) {
    BaseModel.call(this, 'project_updates');

    this.Constructor = ProjectUpdateModel;

    return this.create(method, resource, config);
}

function ProjectUpdateModelLoader (_BaseModel_) {
    BaseModel = _BaseModel_;

    return ProjectUpdateModel;
}

ProjectUpdateModelLoader.$inject = [
    'BaseModel'
];

export default ProjectUpdateModelLoader;
