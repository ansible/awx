let $http;
let BaseModel;

function getStats () {
    if (!this.has('GET', 'id')) {
        return Promise.reject(new Error('No property, id, exists'));
    }

    if (!this.has('GET', 'related.events')) {
        return Promise.reject(new Error('No related property, events, exists'));
    }

    const req = {
        method: 'GET',
        url: `${this.path}${this.get('id')}/events/`,
        params: { event: 'playbook_on_stats' },
    };

    return $http(req)
        .then(({ data }) => {
            if (data.results.length > 0) {
                return data.results[0];
            }

            return null;
        });
}

function ProjectUpdateModel (method, resource, config) {
    BaseModel.call(this, 'project_updates');

    this.getStats = getStats.bind(this);

    this.Constructor = ProjectUpdateModel;

    return this.create(method, resource, config);
}

function ProjectUpdateModelLoader (_$http_, _BaseModel_) {
    $http = _$http_;
    BaseModel = _BaseModel_;

    return ProjectUpdateModel;
}

ProjectUpdateModelLoader.$inject = [
    '$http',
    'BaseModel'
];

export default ProjectUpdateModelLoader;
