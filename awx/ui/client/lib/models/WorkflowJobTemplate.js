let Base;
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
        !launchData.survey_enabled
    );
}

function WorkflowJobTemplateModel (method, resource, config) {
    Base.call(this, 'workflow_job_templates');

    this.Constructor = WorkflowJobTemplateModel;
    this.optionsLaunch = optionsLaunch.bind(this);
    this.getLaunch = getLaunch.bind(this);
    this.postLaunch = postLaunch.bind(this);
    this.getSurveyQuestions = getSurveyQuestions.bind(this);
    this.canLaunchWithoutPrompt = canLaunchWithoutPrompt.bind(this);

    this.model.launch = {};

    return this.create(method, resource, config);
}

function WorkflowJobTemplateModelLoader (BaseModel, _$http_) {
    Base = BaseModel;
    $http = _$http_;

    return WorkflowJobTemplateModel;
}

WorkflowJobTemplateModelLoader.$inject = [
    'BaseModel',
    '$http'
];

export default WorkflowJobTemplateModelLoader;
