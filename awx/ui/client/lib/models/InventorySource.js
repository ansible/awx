let Base;
let WorkflowJobTemplateNode;
let $http;

function setDependentResources (id) {
    this.dependentResources = [
        {
            model: new WorkflowJobTemplateNode(),
            params: {
                unified_job_template: id
            }
        }
    ];
}

function getUpdate (id) {
    const req = {
        method: 'GET',
        url: `${this.path}${id}/update/`
    };

    return $http(req);
}

function postUpdate (id) {
    const req = {
        method: 'POST',
        url: `${this.path}${id}/update/`
    };

    return $http(req);
}

function InventorySourceModel (method, resource, config) {
    Base.call(this, 'inventory_sources');

    this.Constructor = InventorySourceModel;
    this.setDependentResources = setDependentResources.bind(this);
    this.getUpdate = getUpdate.bind(this);
    this.postUpdate = postUpdate.bind(this);

    return this.create(method, resource, config);
}

function InventorySourceModelLoader (
    BaseModel,
    WorkflowJobTemplateNodeModel,
    _$http_
) {
    Base = BaseModel;
    WorkflowJobTemplateNode = WorkflowJobTemplateNodeModel;
    $http = _$http_;

    return InventorySourceModel;
}

InventorySourceModelLoader.$inject = [
    'BaseModel',
    'WorkflowJobTemplateNodeModel',
    '$http'
];

export default InventorySourceModelLoader;
