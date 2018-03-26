let Base;

function UnifiedJobModel (method, resource, config) {
    Base.call(this, 'unified_jobs');

    this.Constructor = UnifiedJobModel;

    return this.create(method, resource, config);
}

function UnifiedJobModelLoader (BaseModel) {
    Base = BaseModel;

    return UnifiedJobModel;
}

UnifiedJobModelLoader.$inject = [
    'BaseModel'
];

export default UnifiedJobModelLoader;
