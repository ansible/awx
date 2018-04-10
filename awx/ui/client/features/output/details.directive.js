const templateUrl = require('~features/output/details.partial.html');

let $http;
let $filter;
let $scope;
let $state;

let error;
let parse;
let prompt;
let resource;
let strings;
let status;
let wait;

let vm;

function mapChoices (choices) {
    if (!choices) return {};
    return Object.assign(...choices.map(([k, v]) => ({ [k]: v })));
}

function getStatusDetails (jobStatus) {
    const unmapped = jobStatus || resource.model.get('status');

    if (!unmapped) {
        return null;
    }

    const choices = mapChoices(resource.model.options('actions.GET.status.choices'));

    const label = 'Status';
    const icon = `fa icon-job-${unmapped}`;
    const value = choices[unmapped];

    return { label, icon, value };
}

function getStartDetails (started) {
    const unfiltered = started || resource.model.get('started');

    const label = 'Started';

    let value;

    if (unfiltered) {
        value = $filter('longDate')(unfiltered);
    } else {
        value = 'Not Started';
    }

    return { label, value };
}

function getFinishDetails (finished) {
    const unfiltered = finished || resource.model.get('finished');

    const label = 'Finished';

    let value;

    if (unfiltered) {
        value = $filter('longDate')(unfiltered);
    } else {
        value = 'Not Finished';
    }

    return { label, value };
}

function getModuleArgDetails () {
    const value = resource.model.get('module_args');
    const label = 'Module Args';

    if (!value) {
        return null;
    }

    return { label, value };
}

function getJobTypeDetails () {
    const unmapped = resource.model.get('job_type');

    if (!unmapped) {
        return null;
    }

    const choices = mapChoices(resource.model.options('actions.GET.job_type.choices'));

    const label = 'Job Type';
    const value = choices[unmapped];

    return { label, value };
}

function getVerbosityDetails () {
    const verbosity = resource.model.get('verbosity');

    if (!verbosity) {
        return null;
    }

    const choices = mapChoices(resource.model.options('actions.GET.verbosity.choices'));

    const label = 'Verbosity';
    const value = choices[verbosity];

    return { label, value };
}

function getSourceWorkflowJobDetails () {
    const sourceWorkflowJob = resource.model.get('summary_fields.source_workflow_job');

    if (!sourceWorkflowJob) {
        return null;
    }

    const link = `/#/workflows/${sourceWorkflowJob.id}`;
    const tooltip = strings.get('resourceTooltips.SOURCE_WORKFLOW_JOB');

    return { link, tooltip };
}

function getJobTemplateDetails () {
    const jobTemplate = resource.model.get('summary_fields.job_template');

    if (!jobTemplate) {
        return null;
    }

    const label = 'Job Template';
    const link = `/#/templates/job_template/${jobTemplate.id}`;
    const value = $filter('sanitize')(jobTemplate.name);
    const tooltip = strings.get('resourceTooltips.JOB_TEMPLATE');

    return { label, link, value, tooltip };
}

function getLaunchedByDetails () {
    const createdBy = resource.model.get('summary_fields.created_by');
    const jobTemplate = resource.model.get('summary_fields.job_template');

    const relatedSchedule = resource.model.get('related.schedule');
    const schedule = resource.model.get('summary_fields.schedule');

    if (!createdBy && !schedule) {
        return null;
    }

    const label = 'Launched By';

    let link;
    let tooltip;
    let value;

    if (createdBy) {
        tooltip = strings.get('resourceTooltips.USER');
        link = `/#/users/${createdBy.id}`;
        value = $filter('sanitize')(createdBy.username);
    } else if (relatedSchedule && jobTemplate) {
        tooltip = strings.get('resourceTooltips.SCHEDULE');
        link = `/#/templates/job_template/${jobTemplate.id}/schedules/${schedule.id}`;
        value = $filter('sanitize')(schedule.name);
    } else {
        tooltip = null;
        link = null;
        value = $filter('sanitize')(schedule.name);
    }

    return { label, link, tooltip, value };
}

function getInventoryDetails () {
    const inventory = resource.model.get('summary_fields.inventory');

    if (!inventory) {
        return null;
    }

    const label = 'Inventory';
    const tooltip = strings.get('resourceTooltips.INVENTORY');
    const value = $filter('sanitize')(inventory.name);

    let link;

    if (inventory.kind === 'smart') {
        link = `/#/inventories/smart/${inventory.id}`;
    } else {
        link = `/#/inventories/inventory/${inventory.id}`;
    }

    return { label, link, tooltip, value };
}

function getProjectDetails () {
    const project = resource.model.get('summary_fields.project');

    if (!project) {
        return null;
    }

    const label = 'Project';
    const link = `/#/projects/${project.id}`;
    const value = $filter('sanitize')(project.name);
    const tooltip = strings.get('resourceTooltips.PROJECT');

    return { label, link, value, tooltip };
}

function getProjectStatusDetails (projectStatus) {
    const project = resource.model.get('summary_fields.project');
    const jobStatus = projectStatus || resource.model.get('summary_fields.project_update.status');

    if (!project) {
        return null;
    }

    return jobStatus;
}

function getProjectUpdateDetails (updateId) {
    const project = resource.model.get('summary_fields.project');
    const jobId = updateId || resource.model.get('summary_fields.project_update.id');

    if (!project) {
        return null;
    }

    const link = `/#/jobz/project/${jobId}`;
    const tooltip = strings.get('resourceTooltips.PROJECT_UPDATE');

    return { link, tooltip };
}

function getSCMRevisionDetails () {
    const label = 'Revision';
    const value = resource.model.get('scm_revision');

    if (!value) {
        return null;
    }

    return { label, value };
}

function getPlaybookDetails () {
    const label = 'Playbook';
    const value = resource.model.get('playbook');

    if (!value) {
        return null;
    }

    return { label, value };
}

function getJobExplanationDetails () {
    const explanation = resource.model.get('job_explanation');

    if (!explanation) {
        return null;
    }

    const limit = 150;
    const label = 'Explanation';

    let more = explanation;

    if (explanation.split(':')[0] === 'Previous Task Failed') {
        const taskStringIndex = explanation.split(':')[0].length + 1;
        const task = JSON.parse(explanation.substring(taskStringIndex));

        more = `${task.job_type} failed for ${task.job_name} with ID ${task.job_id}`;
    }

    const less = $filter('limitTo')(more, limit);

    const showMore = false;
    const hasMoreToShow = more.length > limit;

    return { label, less, more, showMore, hasMoreToShow };
}

function getResultTracebackDetails () {
    const traceback = resource.model.get('result_traceback');

    if (!traceback) {
        return null;
    }

    const limit = 150;
    const label = 'Results Traceback';

    const more = traceback;
    const less = $filter('limitTo')(more, limit);

    const showMore = false;
    const hasMoreToShow = more.length > limit;

    return { label, less, more, showMore, hasMoreToShow };
}

function getCredentialDetails () {
    const credential = resource.model.get('summary_fields.credential');

    if (!credential) {
        return null;
    }

    let label = 'Credential';

    if (resource.type === 'playbook') {
        label = 'Machine Credential';
    }

    if (resource.type === 'inventory') {
        label = 'Source Credential';
    }

    const link = `/#/credentials/${credential.id}`;
    const tooltip = strings.get('resourceTooltips.CREDENTIAL');
    const value = $filter('sanitize')(credential.name);

    return { label, link, tooltip, value };
}

function getForkDetails () {
    const label = 'Forks';
    const value = resource.model.get('forks');

    if (!value) {
        return null;
    }

    return { label, value };
}

function getLimitDetails () {
    const label = 'Limit';
    const value = resource.model.get('limit');

    if (!value) {
        return null;
    }

    return { label, value };
}

function getInstanceGroupDetails () {
    const instanceGroup = resource.model.get('summary_fields.instance_group');

    if (!instanceGroup) {
        return null;
    }

    const label = 'Instance Group';
    const value = $filter('sanitize')(instanceGroup.name);

    let isolated = null;

    if (instanceGroup.controller_id) {
        isolated = 'Isolated';
    }

    return { label, value, isolated };
}

function getJobTagDetails () {
    const label = 'Job Tags';
    const value = resource.model.get('job_tags');

    if (!value) {
        return null;
    }

    return { label, value };
}

function getSkipTagDetails () {
    const label = 'Skip Tags';
    const value = resource.model.get('skip_tags');

    if (!value) {
        return null;
    }

    return { label, value };
}

function getExtraVarsDetails () {
    const extraVars = resource.model.get('extra_vars');

    if (!extraVars) {
        return null;
    }

    const label = 'Extra Variables';
    const tooltip = 'Read-only view of extra variables added to the job template.';
    const value = parse(extraVars);
    const disabled = true;

    return { label, tooltip, value, disabled };
}

function getLabelDetails () {
    const jobLabels = _.get(resource.model.get('related.labels'), 'results', []);

    if (jobLabels.length < 1) {
        return null;
    }

    const label = 'Labels';
    const more = false;

    const value = jobLabels.map(({ name }) => name).map($filter('sanitize'));

    return { label, more, value };
}

function createErrorHandler (path, action) {
    return res => {
        const hdr = strings.get('error.HEADER');
        const msg = strings.get('error.CALL', { path, action, status: res.status });

        error($scope, res.data, res.status, null, { hdr, msg });
    };
}

const ELEMENT_LABELS = '#job-results-labels';
const ELEMENT_PROMPT_MODAL = '#prompt-modal';
const LABELS_SLIDE_DISTANCE = 200;

function toggleLabels () {
    if (!this.labels.more) {
        $(ELEMENT_LABELS).slideUp(LABELS_SLIDE_DISTANCE);
        this.labels.more = true;
    } else {
        $(ELEMENT_LABELS).slideDown(LABELS_SLIDE_DISTANCE);
        this.labels.more = false;
    }
}

function cancelJob () {
    const actionText = strings.get('warnings.CANCEL_ACTION');
    const hdr = strings.get('warnings.CANCEL_HEADER');
    const warning = strings.get('warnings.CANCEL_BODY');

    const id = resource.model.get('id');
    const name = $filter('sanitize')(resource.model.get('name'));

    const body = `<div class="Prompt-bodyQuery">${warning}</div>`;
    const resourceName = `#${id} ${name}`;

    const method = 'POST';
    const url = `${resource.model.path}${id}/cancel/`;

    const errorHandler = createErrorHandler('cancel job', method);

    const action = () => {
        wait('start');
        $http({ method, url })
            .catch(errorHandler)
            .finally(() => {
                $(ELEMENT_PROMPT_MODAL).modal('hide');
                wait('stop');
            });
    };

    prompt({ hdr, resourceName, body, actionText, action });
}

function deleteJob () {
    const actionText = strings.get('DELETE');
    const hdr = strings.get('warnings.DELETE_HEADER');
    const warning = strings.get('warnings.DELETE_BODY');

    const id = resource.model.get('id');
    const name = $filter('sanitize')(resource.model.get('name'));

    const body = `<div class="Prompt-bodyQuery">${warning}</div>`;
    const resourceName = `#${id} ${name}`;

    const method = 'DELETE';
    const url = `${resource.model.path}${id}/`;

    const errorHandler = createErrorHandler('delete job', method);

    const action = () => {
        wait('start');
        $http({ method, url })
            .then(() => $state.go('jobs'))
            .catch(errorHandler)
            .finally(() => {
                $(ELEMENT_PROMPT_MODAL).modal('hide');
                wait('stop');
            });
    };

    prompt({ hdr, resourceName, body, actionText, action });
}

function AtJobDetailsController (
    _$http_,
    _$filter_,
    _$state_,
    _error_,
    _prompt_,
    _strings_,
    _status_,
    _wait_,
    ParseTypeChange,
    ParseVariableString,
) {
    vm = this || {};

    $http = _$http_;
    $filter = _$filter_;
    $state = _$state_;

    error = _error_;
    parse = ParseVariableString;
    prompt = _prompt_;
    strings = _strings_;
    status = _status_;
    wait = _wait_;

    vm.init = _$scope_ => {
        $scope = _$scope_;
        resource = $scope.resource; // eslint-disable-line prefer-destructuring

        vm.status = getStatusDetails();
        vm.started = getStartDetails();
        vm.finished = getFinishDetails();
        vm.moduleArgs = getModuleArgDetails();
        vm.jobType = getJobTypeDetails();
        vm.jobTemplate = getJobTemplateDetails();
        vm.sourceWorkflowJob = getSourceWorkflowJobDetails();
        vm.inventory = getInventoryDetails();
        vm.project = getProjectDetails();
        vm.projectUpdate = getProjectUpdateDetails();
        vm.projectStatus = getProjectStatusDetails();
        vm.scmRevision = getSCMRevisionDetails();
        vm.playbook = getPlaybookDetails();
        vm.resultTraceback = getResultTracebackDetails();
        vm.launchedBy = getLaunchedByDetails();
        vm.jobExplanation = getJobExplanationDetails();
        vm.verbosity = getVerbosityDetails();
        vm.credential = getCredentialDetails();
        vm.forks = getForkDetails();
        vm.limit = getLimitDetails();
        vm.instanceGroup = getInstanceGroupDetails();
        vm.jobTags = getJobTagDetails();
        vm.skipTags = getSkipTagDetails();
        vm.extraVars = getExtraVarsDetails();
        vm.labels = getLabelDetails();

        // Relaunch and Delete Components
        vm.job = _.get(resource.model, 'model.GET', {});
        vm.canDelete = resource.model.get('summary_fields.user_capabilities.delete');

        vm.cancelJob = cancelJob;
        vm.deleteJob = deleteJob;
        vm.toggleLabels = toggleLabels;

        const observe = (getter, transform, key) => {
            $scope.$watch(getter, value => { vm[key] = transform(value); });
        };

        observe(status.getStarted, getStartDetails, 'started');
        observe(status.getJobStatus, getStatusDetails, 'status');
        observe(status.getFinished, getFinishDetails, 'finished');
        observe(status.getProjectUpdateId, getProjectUpdateDetails, 'projectUpdate');
        observe(status.getProjectStatus, getProjectStatusDetails, 'projectStatus');
    };
}

AtJobDetailsController.$inject = [
    '$http',
    '$filter',
    '$state',
    'ProcessErrors',
    'Prompt',
    'JobStrings',
    'JobStatusService',
    'Wait',
    'ParseTypeChange',
    'ParseVariableString',
];

function atJobDetailsLink (scope, el, attrs, controllers) {
    const [atDetailsController] = controllers;

    atDetailsController.init(scope);
}

function atJobDetails () {
    return {
        templateUrl,
        restrict: 'E',
        require: ['atJobDetails'],
        controllerAs: 'vm',
        link: atJobDetailsLink,
        controller: AtJobDetailsController,
        scope: { resource: '=', },
    };
}

export default atJobDetails;
