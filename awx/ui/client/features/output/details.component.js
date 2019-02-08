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
    const label = strings.get('labels.STATUS');

    let icon;
    let value;

    if (unmapped === 'unknown') {
        icon = 'fa icon-job-pending';
        value = strings.get('details.UNKNOWN');
    } else {
        icon = `fa icon-job-${unmapped}`;
        value = choices[unmapped];
    }

    return { label, icon, value };
}

function getStartDetails (started) {
    const unfiltered = started || resource.model.get('started');
    const label = strings.get('labels.STARTED');

    let value;

    if (unfiltered) {
        value = $filter('longDate')(unfiltered);
    } else {
        value = strings.get('details.NOT_STARTED');
    }

    return { label, value };
}

function getFinishDetails (finished) {
    const unfiltered = finished || resource.model.get('finished');
    const label = strings.get('labels.FINISHED');

    let value;

    if (unfiltered) {
        value = $filter('longDate')(unfiltered);
    } else {
        value = strings.get('details.NOT_FINISHED');
    }

    return { label, value };
}

function getModuleArgDetails () {
    const value = resource.model.get('module_args');
    const label = strings.get('labels.MODULE_ARGS');

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

    const label = strings.get('labels.JOB_TYPE');
    const value = choices[unmapped];

    return { label, value };
}

function getVerbosityDetails () {
    const verbosity = resource.model.get('verbosity');

    if (!verbosity) {
        return null;
    }

    const choices = mapChoices(resource.model.options('actions.GET.verbosity.choices'));

    const label = strings.get('labels.VERBOSITY');
    const value = choices[verbosity];

    return { label, value };
}

function getEnvironmentDetails (virtualenv) {
    const customVirtualenv = virtualenv || resource.model.get('custom_virtualenv');

    if (!customVirtualenv || customVirtualenv === '') {
        return null;
    }

    const label = strings.get('labels.ENVIRONMENT');
    const value = $filter('sanitize')(customVirtualenv);

    return { label, value };
}

function getSourceWorkflowJobDetails () {
    const sourceWorkflowJob = resource.model.get('summary_fields.source_workflow_job');

    if (!sourceWorkflowJob) {
        return null;
    }

    const label = strings.get('labels.SOURCE_WORKFLOW_JOB');
    const value = sourceWorkflowJob.name;
    const link = `/#/workflows/${sourceWorkflowJob.id}`;
    const tooltip = strings.get('tooltips.SOURCE_WORKFLOW_JOB');

    return { label, value, link, tooltip };
}

function getSliceJobDetails () {
    const count = resource.model.get('job_slice_count');

    if (!count) {
        return null;
    }

    if (count === 1) {
        return null;
    }

    const number = resource.model.get('job_slice_number');

    if (!number) {
        return null;
    }

    const label = strings.get('labels.SLICE_JOB');
    const offset = `${number}/${count}`;
    const tooltip = strings.get('tooltips.SLICE_JOB_DETAILS');

    if (label && offset && tooltip) {
        return { label, offset, tooltip };
    }
    return null;
}

function getJobTemplateDetails () {
    const jobTemplate = resource.model.get('summary_fields.job_template');

    if (!jobTemplate) {
        return null;
    }

    const label = strings.get('labels.JOB_TEMPLATE');
    const link = `/#/templates/job_template/${jobTemplate.id}`;
    const value = $filter('sanitize')(jobTemplate.name);
    const tooltip = strings.get('tooltips.JOB_TEMPLATE');

    return { label, link, value, tooltip };
}

function getInventorySourceDetails () {
    if (!resource.model.has('summary_fields.inventory_source.source')) {
        return null;
    }

    if (resource.model.get('summary_fields.inventory_source.source') === 'scm') {
        // we already show a SOURCE PROJECT item for scm inventory updates, so we
        // skip the display of the standard source details item.
        return null;
    }

    const { source } = resource.model.get('summary_fields.inventory_source');
    const choices = mapChoices(resource.model.options('actions.GET.source.choices'));

    const label = strings.get('labels.SOURCE');
    const value = choices[source];

    return { label, value };
}

function getOverwriteDetails () {
    if (!resource.model.has('overwrite')) {
        return null;
    }

    const label = strings.get('labels.OVERWRITE');
    const value = resource.model.get('overwrite');

    return { label, value };
}

function getOverwriteVarsDetails () {
    if (!resource.model.has('overwrite_vars')) {
        return null;
    }

    const label = strings.get('labels.OVERWRITE_VARS');
    const value = resource.model.get('overwrite_vars');

    return { label, value };
}

function getCompatibilityModeDetails () {
    if (!resource.model.has('compatibility_mode')) {
        return null;
    }

    const label = strings.get('labels.COMPATIBILITY_MODE');
    const value = resource.model.get('compatibility_mode');

    return { label, value };
}

function getLicenseErrorDetails () {
    if (!resource.model.has('license_error')) {
        return null;
    }

    const label = strings.get('labels.LICENSE_ERROR');
    const value = resource.model.get('license_error');

    return { label, value };
}

function getHostLimitErrorDetails () {
    if (!resource.model.has('org_host_limit_error')) {
        return null;
    }

    const label = strings.get('labels.HOST_LIMIT_ERROR');
    const tooltip = strings.get('tooltips.HOST_LIMIT');
    const value = resource.model.get('org_host_limit_error');

    return { tooltip, label, value };
}

function getLaunchedByDetails () {
    const createdBy = resource.model.get('summary_fields.created_by');
    const jobTemplate = resource.model.get('summary_fields.job_template');
    const relatedSchedule = resource.model.get('related.schedule');
    const schedule = resource.model.get('summary_fields.schedule');

    if (!createdBy && !schedule) {
        return null;
    }

    const label = strings.get('labels.LAUNCHED_BY');

    let link;
    let tooltip;
    let value;

    if (createdBy) {
        tooltip = strings.get('tooltips.USER');
        link = `/#/users/${createdBy.id}`;
        value = $filter('sanitize')(createdBy.username);
    } else if (relatedSchedule && jobTemplate) {
        tooltip = strings.get('tooltips.SCHEDULE');
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

    const label = strings.get('labels.INVENTORY');
    const tooltip = strings.get('tooltips.INVENTORY');
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

    const label = strings.get('labels.PROJECT');
    const link = `/#/projects/${project.id}`;
    const value = project.name;
    const tooltip = strings.get('tooltips.PROJECT');

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
    const tooltip = strings.get('tooltips.PROJECT_UPDATE');

    return { link, tooltip };
}

function getInventoryScmDetails (updateId, updateStatus) {
    const projectId = resource.model.get('summary_fields.source_project.id');
    const projectName = resource.model.get('summary_fields.source_project.name');
    const jobId = updateId || resource.model.get('source_project_update');
    const status = updateStatus || resource.model.get('summary_fields.inventory_source.status');

    if (!projectId || !projectName) {
        return null;
    }

    const label = strings.get('labels.INVENTORY_SCM');
    const jobLink = `/#/jobs/project/${jobId}`;
    const link = `/#/projects/${projectId}`;
    const jobTooltip = strings.get('tooltips.INVENTORY_SCM_JOB');
    const tooltip = strings.get('tooltips.INVENTORY_SCM');
    const value = $filter('sanitize')(projectName);

    let icon;

    if (status === 'unknown') {
        icon = 'fa icon-job-pending';
    } else {
        icon = `fa icon-job-${status}`;
    }

    return { label, link, icon, jobLink, jobTooltip, tooltip, value };
}

function getSCMRevisionDetails () {
    const label = strings.get('labels.SCM_REVISION');
    const value = resource.model.get('scm_revision');

    if (!value) {
        return null;
    }

    return { label, value };
}

function getPlaybookDetails () {
    const label = strings.get('labels.PLAYBOOK');
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
    const label = strings.get('labels.JOB_EXPLANATION');

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
    const label = strings.get('labels.RESULT_TRACEBACK');

    const more = traceback;
    const less = $filter('limitTo')(more, limit);

    const showMore = false;
    const hasMoreToShow = more.length > limit;

    return { label, less, more, showMore, hasMoreToShow };
}

function getCredentialDetails () {
    let credentials = [];
    let credentialTags = [];

    if (resource.model.get('type') === 'job') {
        credentials = resource.model.get('summary_fields.credentials');
    } else {
        const credential = resource.model.get('summary_fields.credential');
        if (credential) {
            credentials.push(credential);
        }
    }

    if (!credentials || credentials.length < 1) {
        return null;
    }

    credentialTags = credentials.map((cred) => buildCredentialDetails(cred));

    const label = strings.get('labels.CREDENTIAL');
    const value = credentialTags;

    return { label, value };
}

function buildCredentialDetails (credential) {
    const icon = `${credential.kind}`;
    const link = `/#/credentials/${credential.id}`;
    const tooltip = strings.get('tooltips.CREDENTIAL');
    const value = $filter('sanitize')(credential.name);

    return { icon, link, tooltip, value };
}

function getForkDetails () {
    const label = strings.get('labels.FORKS');
    const value = resource.model.get('forks');

    if (!value) {
        return null;
    }

    return { label, value };
}

function getLimitDetails () {
    const label = strings.get('labels.LIMIT');
    const value = resource.model.get('limit');

    if (!value) {
        return null;
    }

    return { label, value };
}

function getExecutionNodeDetails (node) {
    const executionNode = node || resource.model.get('execution_node');

    if (!executionNode) {
        return null;
    }

    const label = strings.get('labels.EXECUTION_NODE');
    const value = $filter('sanitize')(executionNode);

    return { label, value };
}

function getInstanceGroupDetails () {
    const instanceGroup = resource.model.get('summary_fields.instance_group');

    if (!instanceGroup) {
        return null;
    }

    const label = strings.get('labels.INSTANCE_GROUP');
    const value = $filter('sanitize')(instanceGroup.name);
    const link = `/#/instance_groups/${instanceGroup.id}`;

    let isolated = null;

    if (instanceGroup.controller_id) {
        isolated = strings.get('details.ISOLATED');
    }

    return { label, value, isolated, link };
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

    const label = strings.get('labels.JOB_TAGS');
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

    const more = false;
    const label = strings.get('labels.SKIP_TAGS');
    const value = skipTags.map($filter('sanitize'));

    return { label, more, value };
}

function getExtraVarsDetails () {
    const extraVars = resource.model.get('extra_vars');

    if (!extraVars) {
        return null;
    }

    const label = strings.get('labels.EXTRA_VARS');
    const tooltip = strings.get('tooltips.EXTRA_VARS');
    const value = parse(extraVars);
    const disabled = true;
    const name = 'extra_vars';

    return { label, tooltip, value, disabled, name };
}

function getArtifactsDetails (val) {
    const artifacts = val || resource.model.get('artifacts');
    if (!artifacts || (Object.entries(artifacts).length === 0 &&
        artifacts.constructor === Object)) {
        return null;
    }

    const label = strings.get('labels.ARTIFACTS');
    const tooltip = strings.get('tooltips.ARTIFACTS');
    const value = parse(artifacts);
    const disabled = true;
    const name = 'artifacts';

    return { label, tooltip, value, disabled, name };
}

function getLabelDetails () {
    const jobLabels = _.get(resource.model.get('summary_fields.labels'), 'results', []);

    if (jobLabels.length < 1) {
        return null;
    }

    const label = strings.get('labels.LABELS');
    const more = false;
    const value = jobLabels.map(({ name }) => name).map($filter('sanitize'));
    const truncate = true;
    const truncateLength = 5;
    const hasMoreToShow = jobLabels.length > truncateLength;

    return { label, more, hasMoreToShow, value, truncate, truncateLength };
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

function showLabels () {
    this.labels.truncate = !this.labels.truncate;

    const jobLabelsCount = _.get(resource.model.get('summary_fields.labels'), 'count');
    const maxCount = 50;

    if (this.labels.value.length === jobLabelsCount || this.labels.value.length >= maxCount) {
        return;
    }

    const config = {
        params: {
            page_size: maxCount
        }
    };

    wait('start');
    resource.model.extend('get', 'labels', config)
        .then((model) => {
            const jobLabels = _.get(model.get('related.labels'), 'results', []);
            this.labels.value = jobLabels.map(({ name }) => name).map($filter('sanitize'));
        })
        .catch(createErrorHandler('get labels', 'GET'))
        .finally(() => wait('stop'));
}

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
        vm.strings = strings;

        vm.status = getStatusDetails();
        vm.started = getStartDetails();
        vm.finished = getFinishDetails();
        vm.moduleArgs = getModuleArgDetails();
        vm.jobType = getJobTypeDetails();
        vm.jobTemplate = getJobTemplateDetails();
        vm.sourceWorkflowJob = getSourceWorkflowJobDetails();
        vm.sliceJobDetails = getSliceJobDetails();
        vm.inventory = getInventoryDetails();
        vm.project = getProjectDetails();
        vm.projectUpdate = getProjectUpdateDetails();
        vm.projectStatus = getProjectStatusDetails();
        vm.scmRevision = getSCMRevisionDetails();
        vm.inventoryScm = getInventoryScmDetails();
        vm.playbook = getPlaybookDetails();
        vm.resultTraceback = getResultTracebackDetails();
        vm.launchedBy = getLaunchedByDetails();
        vm.jobExplanation = getJobExplanationDetails();
        vm.verbosity = getVerbosityDetails();
        vm.environment = getEnvironmentDetails();
        vm.credentials = getCredentialDetails();
        vm.forks = getForkDetails();
        vm.limit = getLimitDetails();
        vm.executionNode = getExecutionNodeDetails();
        vm.instanceGroup = getInstanceGroupDetails();
        vm.jobTags = getJobTagDetails();
        vm.skipTags = getSkipTagDetails();
        vm.extraVars = getExtraVarsDetails();
        vm.artifacts = getArtifactsDetails();
        vm.labels = getLabelDetails();
        vm.inventorySource = getInventorySourceDetails();
        vm.overwrite = getOverwriteDetails();
        vm.overwriteVars = getOverwriteVarsDetails();
        vm.compatibilityMode = getCompatibilityModeDetails();
        vm.licenseError = getLicenseErrorDetails();
        vm.hostLimitError = getHostLimitErrorDetails();

        // Relaunch and Delete Components
        vm.job = angular.copy(_.get(resource.model, 'model.GET', {}));
        vm.canDelete = resource.model.get('summary_fields.user_capabilities.delete');

        vm.cancelJob = cancelJob;
        vm.deleteJob = deleteJob;
        vm.toggleJobTags = toggleJobTags;
        vm.toggleSkipTags = toggleSkipTags;
        vm.toggleLabels = toggleLabels;
        vm.showLabels = showLabels;

        unsubscribe = subscribe(({
            status,
            started,
            finished,
            scm,
            inventoryScm,
            environment,
            artifacts,
            executionNode
        }) => {
            vm.started = getStartDetails(started);
            vm.finished = getFinishDetails(finished);
            vm.projectUpdate = getProjectUpdateDetails(scm.id);
            vm.projectStatus = getProjectStatusDetails(scm.status);
            vm.environment = getEnvironmentDetails(environment);
            vm.artifacts = getArtifactsDetails(artifacts);
            vm.executionNode = getExecutionNodeDetails(executionNode);
            vm.inventoryScm = getInventoryScmDetails(inventoryScm.id, inventoryScm.status);
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
    'OutputStrings',
    'Wait',
    'ParseVariableString',
    'OutputStatusService',
];

export default {
    templateUrl,
    controller: JobDetailsController,
    controllerAs: 'vm',
    bindings: {
        resource: '<'
    },
};
