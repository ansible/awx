const templateUrl = require('~features/output/details.partial.html');

let $http;
let $filter;
let $state;

let error;
let parse;
let prompt;
let resource;
let strings;
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

function getInventoryJobNameDetails () {
    if (resource.model.get('type') !== 'inventory_update') {
        return null;
    }

    const jobArgs = resource.model.get('job_args');

    if (!jobArgs) {
        return null;
    }

    let parsedJobArgs;

    try {
        parsedJobArgs = JSON.parse(jobArgs);
    } catch (e) {
        return null;
    }

    if (!Array.isArray(parsedJobArgs)) {
        return null;
    }

    const jobArgIndex = parsedJobArgs.indexOf('--inventory-id');
    const inventoryId = parsedJobArgs[jobArgIndex + 1];

    if (jobArgIndex < 0) {
        return null;
    }

    if (!Number.isInteger(parseInt(inventoryId, 10))) {
        return null;
    }

    const name = resource.model.get('name');
    const id = resource.model.get('id');

    const label = 'Name';
    const tooltip = strings.get('resourceTooltips.INVENTORY');
    const value = `${id} - ${$filter('sanitize')(name)}`;
    const link = `/#/inventories/inventory/${inventoryId}`;

    return { label, link, tooltip, value };
}

function getInventorySourceDetails () {
    if (!resource.model.has('summary_fields.inventory_source.source')) {
        return null;
    }

    const { source } = resource.model.get('summary_fields.inventory_source');
    const choices = mapChoices(resource.model.options('actions.GET.source.choices'));

    const label = 'Source';
    const value = choices[source];

    return { label, value };
}

function getOverwriteDetails () {
    if (!resource.model.has('overwrite')) {
        return null;
    }

    const label = 'Overwrite';
    const value = resource.model.get('overwrite');

    return { label, value };
}

function getOverwriteVarsDetails () {
    if (!resource.model.has('overwrite_vars')) {
        return null;
    }

    const label = 'Overwrite Vars';
    const value = resource.model.get('overwrite_vars');

    return { label, value };
}

function getLicenseErrorDetails () {
    if (!resource.model.has('license_error')) {
        return null;
    }

    const label = 'License Error';
    const value = resource.model.get('license_error');

    return { label, value };
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

    const link = `/#/jobs/project/${jobId}`;
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
    const label = 'Error Details';

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
    const tagString = resource.model.get('job_tags');

    let jobTags;

    if (tagString) {
        jobTags = tagString.split(',').filter(tag => tag !== '');
    } else {
        jobTags = [];
    }

    if (jobTags.length < 1) {
        return null;
    }

    const label = 'Job Tags';
    const more = false;

    const value = jobTags.map($filter('sanitize'));

    return { label, more, value };
}

function getSkipTagDetails () {
    const tagString = resource.model.get('skip_tags');

    let skipTags;

    if (tagString) {
        skipTags = tagString.split(',').filter(tag => tag !== '');
    } else {
        skipTags = [];
    }

    if (skipTags.length < 1) {
        return null;
    }

    const label = 'Skip Tags';
    const more = false;
    const value = skipTags.map($filter('sanitize'));

    return { label, more, value };
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

        error(null, res.data, res.status, null, { hdr, msg });
    };
}

const ELEMENT_LABELS = '#job-results-labels';
const ELEMENT_JOB_TAGS = '#job-results-job-tags';
const ELEMENT_SKIP_TAGS = '#job-results-skip-tags';
const ELEMENT_PROMPT_MODAL = '#prompt-modal';
const TAGS_SLIDE_DISTANCE = 200;

function toggleLabels () {
    if (!this.labels.more) {
        $(ELEMENT_LABELS).slideUp(TAGS_SLIDE_DISTANCE);
        this.labels.more = true;
    } else {
        $(ELEMENT_LABELS).slideDown(TAGS_SLIDE_DISTANCE);
        this.labels.more = false;
    }
}

function toggleJobTags () {
    if (!this.jobTags.more) {
        $(ELEMENT_JOB_TAGS).slideUp(TAGS_SLIDE_DISTANCE);
        this.jobTags.more = true;
    } else {
        $(ELEMENT_JOB_TAGS).slideDown(TAGS_SLIDE_DISTANCE);
        this.jobTags.more = false;
    }
}

function toggleSkipTags () {
    if (!this.skipTags.more) {
        $(ELEMENT_SKIP_TAGS).slideUp(TAGS_SLIDE_DISTANCE);
        this.skipTags.more = true;
    } else {
        $(ELEMENT_SKIP_TAGS).slideDown(TAGS_SLIDE_DISTANCE);
        this.skipTags.more = false;
    }
}

function cancelJob () {
    const actionText = strings.get('cancelJob.CANCEL_JOB');
    const hdr = strings.get('cancelJob.HEADER');
    const warning = strings.get('cancelJob.SUBMIT_REQUEST');
    const cancelText = strings.get('cancelJob.RETURN');

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

    prompt({ hdr, resourceName, body, actionText, action, cancelText });
}

function deleteJob () {
    const actionText = strings.get('DELETE');
    const hdr = strings.get('deleteResource.HEADER');
    const warning = strings.get('deleteResource.CONFIRM', 'job');

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

function JobDetailsController (
    _$http_,
    _$filter_,
    _$state_,
    _error_,
    _prompt_,
    _strings_,
    _wait_,
    _parse_,
    { subscribe },
) {
    vm = this || {};

    $http = _$http_;
    $filter = _$filter_;
    $state = _$state_;
    error = _error_;

    parse = _parse_;
    prompt = _prompt_;
    strings = _strings_;
    wait = _wait_;

    let unsubscribe;

    vm.$onInit = () => {
        resource = this.resource; // eslint-disable-line prefer-destructuring

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
        vm.inventoryJobName = getInventoryJobNameDetails();
        vm.inventorySource = getInventorySourceDetails();
        vm.overwrite = getOverwriteDetails();
        vm.overwriteVars = getOverwriteVarsDetails();
        vm.licenseError = getLicenseErrorDetails();

        // Relaunch and Delete Components
        vm.job = angular.copy(_.get(resource.model, 'model.GET', {}));
        vm.canDelete = resource.model.get('summary_fields.user_capabilities.delete');

        vm.cancelJob = cancelJob;
        vm.deleteJob = deleteJob;
        vm.toggleJobTags = toggleJobTags;
        vm.toggleSkipTags = toggleSkipTags;
        vm.toggleLabels = toggleLabels;

        unsubscribe = subscribe(({ status, started, finished, scm }) => {
            vm.started = getStartDetails(started);
            vm.finished = getFinishDetails(finished);
            vm.projectUpdate = getProjectUpdateDetails(scm.id);
            vm.projectStatus = getProjectStatusDetails(scm.status);
            vm.status = getStatusDetails(status);
            vm.job.status = status;
        });
    };

    vm.$onDestroy = () => {
        unsubscribe();
    };
}

JobDetailsController.$inject = [
    '$http',
    '$filter',
    '$state',
    'ProcessErrors',
    'Prompt',
    'JobStrings',
    'Wait',
    'ParseVariableString',
    'JobStatusService',
];

export default {
    templateUrl,
    controller: JobDetailsController,
    controllerAs: 'vm',
    bindings: {
        resource: '<'
    },
};
