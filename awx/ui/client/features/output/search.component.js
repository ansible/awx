const templateUrl = require('~features/output/search.partial.html');

const searchReloadOptions = { reload: true, inherit: false };
const searchKeyExamples = ['id:>1', 'task:set', 'created:>=2000-01-01'];
const searchKeyFields = ['changed', 'failed', 'host_name', 'stdout', 'task', 'role', 'playbook', 'play'];

const PLACEHOLDER_RUNNING = 'CANNOT SEARCH RUNNING JOB';
const PLACEHOLDER_DEFAULT = 'SEARCH';

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

function removeSearchTag (index) {
    const searchTerm = vm.tags[index];

    const currentQueryset = getCurrentQueryset();
    const modifiedQueryset = qs.removeTermsFromQueryset(currentQueryset, searchTerm);

    vm.tags = getSearchTags(modifiedQueryset);
    vm.disabled = true;

    $state.params.job_event_search = qs.encodeArr(modifiedQueryset);
    $state.transitionTo($state.current, $state.params, searchReloadOptions);
}

function submitSearch () {
    const searchInputQueryset = qs.getSearchInputQueryset(vm.value);

    const currentQueryset = getCurrentQueryset();
    const modifiedQueryset = qs.mergeQueryset(currentQueryset, searchInputQueryset);

    vm.tags = getSearchTags(modifiedQueryset);
    vm.disabled = true;

    $state.params.job_event_search = qs.encodeArr(modifiedQueryset);
    $state.transitionTo($state.current, $state.params, searchReloadOptions);
}

function clearSearch () {
    vm.tags = [];
    vm.disabled = true;

    $state.params.job_event_search = '';
    $state.transitionTo($state.current, $state.params, searchReloadOptions);
}

function JobSearchController (_$state_, _qs_, { subscribe }) {
    $state = _$state_;
    qs = _qs_;

    vm = this || {};

    vm.value = '';
    vm.key = false;
    vm.rejected = false;
    vm.disabled = true;
    vm.tags = getSearchTags(getCurrentQueryset());

    vm.clearSearch = clearSearch;
    vm.searchKeyExamples = searchKeyExamples;
    vm.searchKeyFields = searchKeyFields;
    vm.toggleSearchKey = toggleSearchKey;
    vm.removeSearchTag = removeSearchTag;
    vm.submitSearch = submitSearch;

    let unsubscribe;

    vm.$onInit = () => {
        vm.examples = searchKeyExamples;
        vm.fields = searchKeyFields;
        vm.placeholder = PLACEHOLDER_DEFAULT;
        vm.relatedFields = [];

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
