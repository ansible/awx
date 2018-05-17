const templateUrl = require('~features/output/search.partial.html');

const searchReloadOptions = { inherit: false, location: 'replace' };
const searchKeyExamples = ['id:>1', 'task:set', 'created:>=2000-01-01'];
const searchKeyFields = ['changed', 'failed', 'host_name', 'stdout', 'task', 'role', 'playbook', 'play'];

const PLACEHOLDER_RUNNING = 'CANNOT SEARCH RUNNING JOB';
const PLACEHOLDER_DEFAULT = 'SEARCH';
const REJECT_DEFAULT = 'Failed to update search results.';
const REJECT_INVALID = 'Invalid search filter provided.';

let $state;
let qs;

let vm;

function toggleSearchKey () {
    vm.key = !vm.key;
}

function getCurrentQueryset () {
    const { job_event_search } = $state.params; // eslint-disable-line camelcase

    return qs.decodeArr(job_event_search);
}

function getSearchTags (queryset) {
    return qs.createSearchTagsFromQueryset(queryset)
        .filter(tag => !tag.startsWith('event'))
        .filter(tag => !tag.startsWith('-event'))
        .filter(tag => !tag.startsWith('page_size'))
        .filter(tag => !tag.startsWith('order_by'));
}

function reloadQueryset (queryset, rejection = REJECT_DEFAULT) {
    const params = angular.copy($state.params);
    const currentTags = vm.tags;

    params.handleErrors = false;
    params.job_event_search = qs.encodeArr(queryset);

    vm.disabled = true;
    vm.message = '';
    vm.tags = getSearchTags(queryset);

    return $state.transitionTo($state.current, params, searchReloadOptions)
        .catch(() => {
            vm.tags = currentTags;
            vm.message = rejection;
            vm.rejected = true;
            vm.disabled = false;
        });
}

function removeSearchTag (index) {
    const searchTerm = vm.tags[index];

    const currentQueryset = getCurrentQueryset();
    const modifiedQueryset = qs.removeTermsFromQueryset(currentQueryset, searchTerm);

    reloadQueryset(modifiedQueryset);
}

function submitSearch () {
    const currentQueryset = getCurrentQueryset();

    const searchInputQueryset = qs.getSearchInputQueryset(vm.value);
    const modifiedQueryset = qs.mergeQueryset(currentQueryset, searchInputQueryset);

    reloadQueryset(modifiedQueryset, REJECT_INVALID);
}

function clearSearch () {
    reloadQueryset();
}

function JobSearchController (_$state_, _qs_, { subscribe }) {
    $state = _$state_;
    qs = _qs_;

    vm = this || {};

    vm.examples = searchKeyExamples;
    vm.fields = searchKeyFields;
    vm.relatedFields = [];
    vm.placeholder = PLACEHOLDER_DEFAULT;

    vm.clearSearch = clearSearch;
    vm.toggleSearchKey = toggleSearchKey;
    vm.removeSearchTag = removeSearchTag;
    vm.submitSearch = submitSearch;

    let unsubscribe;

    vm.$onInit = () => {
        vm.value = '';
        vm.message = '';
        vm.key = false;
        vm.rejected = false;
        vm.disabled = true;
        vm.tags = getSearchTags(getCurrentQueryset());

        unsubscribe = subscribe(({ running }) => {
            vm.disabled = running;
            vm.placeholder = running ? PLACEHOLDER_RUNNING : PLACEHOLDER_DEFAULT;
        });
    };

    vm.$onDestroy = () => {
        unsubscribe();
    };
}

JobSearchController.$inject = [
    '$state',
    'QuerySet',
    'JobStatusService',
];

export default {
    templateUrl,
    controller: JobSearchController,
    controllerAs: 'vm',
};
