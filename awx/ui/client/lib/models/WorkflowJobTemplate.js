/* eslint camelcase: 0 */
let Base;
let $http;
let $q;

function optionsLaunch (id) {
    const req = {
        method: 'OPTIONS',
        url: `${this.path}${id}/launch/`
    };

    return $http(req);
}

function getLaunch (id) {
    const urls = [
        `${this.path}${id}/`,
        `${this.path}${id}/launch/`,
    ];

    const promises = urls.map(url => $http({ method: 'GET', url }));

    return $q.all(promises)
        .then(([res, launchRes]) => {
            this.model.GET = res.data;
            this.model.launch.GET = launchRes.data;

            return launchRes;
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

function getLaunchConf () {
    // We may need api updates to align /:id/launch data with what is returned for job templates.
    // For now, we splice values from the different endpoints to get the launchData we need.
    const {
        ask_inventory_on_launch,
        ask_variables_on_launch,
        survey_enabled,
    } = this.model.GET;

    const {
        can_start_without_user_input,
        variables_needed_to_start,
    } = this.model.launch.GET;

    const launchConf = {
        ask_inventory_on_launch,
        ask_variables_on_launch,
        can_start_without_user_input,
        survey_enabled,
        variables_needed_to_start,
    };

    return launchConf;
}

function canLaunchWithoutPrompt () {
    const launchData = this.getLaunchConf();

    return (
        launchData.can_start_without_user_input &&
        !launchData.ask_inventory_on_launch &&
        !launchData.ask_variables_on_launch &&
        !launchData.survey_enabled &&
        launchData.variables_needed_to_start.length === 0
    );
}

function WorkflowJobTemplateModel (method, resource, config) {
    Base.call(this, 'workflow_job_templates');

    this.Constructor = WorkflowJobTemplateModel;
    this.optionsLaunch = optionsLaunch.bind(this);
    this.getLaunch = getLaunch.bind(this);
    this.postLaunch = postLaunch.bind(this);
    this.getSurveyQuestions = getSurveyQuestions.bind(this);
    this.getLaunchConf = getLaunchConf.bind(this);
    this.canLaunchWithoutPrompt = canLaunchWithoutPrompt.bind(this);

    this.model.launch = {};

    return this.create(method, resource, config);
}

function WorkflowJobTemplateModelLoader (BaseModel, _$http_, _$q_) {
    Base = BaseModel;
    $http = _$http_;
    $q = _$q_;

    return WorkflowJobTemplateModel;
}

WorkflowJobTemplateModelLoader.$inject = [
    'BaseModel',
    '$http',
    '$q',
];

export default WorkflowJobTemplateModelLoader;
