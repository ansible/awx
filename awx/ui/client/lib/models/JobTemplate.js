let Base;
let WorkflowJobTemplateNode;
let $http;

function optionsLaunch (id) {
    const req = {
        method: 'OPTIONS',
        url: `${this.path}${id}/launch/`
    };

    return $http(req);
}

function getLaunch (id) {
    const req = {
        method: 'GET',
        url: `${this.path}${id}/launch/`
    };

    return $http(req)
        .then(res => {
            this.model.launch.GET = res.data;

            return res;
        });
}

function postLaunch (params) {
    const req = {
        method: 'POST',
        url: `${this.path}${params.id}/launch/`
    };

    if (params.launchData) {
        req.data = params.launchData;
    }

    return $http(req);
}

function getSurveyQuestions (id) {
    const req = {
        method: 'GET',
        url: `${this.path}${id}/survey_spec/`
    };

    return $http(req);
}

function canLaunchWithoutPrompt () {
    const launchData = this.model.launch.GET;

    return (
        launchData.can_start_without_user_input &&
        !launchData.ask_inventory_on_launch &&
        !launchData.ask_credential_on_launch &&
        !launchData.ask_verbosity_on_launch &&
        !launchData.ask_job_type_on_launch &&
        !launchData.ask_limit_on_launch &&
        !launchData.ask_tags_on_launch &&
        !launchData.ask_skip_tags_on_launch &&
        !launchData.ask_variables_on_launch &&
        !launchData.ask_diff_mode_on_launch &&
        !launchData.survey_enabled
    );
}

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

function JobTemplateModel (method, resource, config) {
    Base.call(this, 'job_templates');

    this.Constructor = JobTemplateModel;
    this.setDependentResources = setDependentResources.bind(this);
    this.optionsLaunch = optionsLaunch.bind(this);
    this.getLaunch = getLaunch.bind(this);
    this.postLaunch = postLaunch.bind(this);
    this.getSurveyQuestions = getSurveyQuestions.bind(this);
    this.canLaunchWithoutPrompt = canLaunchWithoutPrompt.bind(this);

    this.model.launch = {};

    return this.create(method, resource, config);
}

function JobTemplateModelLoader (BaseModel, WorkflowJobTemplateNodeModel, _$http_) {
    Base = BaseModel;
    WorkflowJobTemplateNode = WorkflowJobTemplateNodeModel;
    $http = _$http_;

    return JobTemplateModel;
}

JobTemplateModelLoader.$inject = [
    'BaseModel',
    'WorkflowJobTemplateNodeModel',
    '$http',
    '$state'
];

export default JobTemplateModelLoader;
