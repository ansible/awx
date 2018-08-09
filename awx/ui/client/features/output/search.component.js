import {
    OUTPUT_SEARCH_DOCLINK,
    OUTPUT_SEARCH_FIELDS,
    OUTPUT_SEARCH_KEY_EXAMPLES,
} from './constants';

const templateUrl = require('~features/output/search.partial.html');

let $state;
let qs;
let strings;

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

function reloadQueryset (queryset, rejection = strings.get('search.REJECT_DEFAULT')) {
    const params = angular.copy($state.params);
    const currentTags = vm.tags;

    params.handleErrors = false;
    params.job_event_search = qs.encodeArr(queryset);

    vm.disabled = true;
    vm.message = '';
    vm.tags = getSearchTags(queryset);

    return vm.reload(params)
        .catch(() => {
            vm.tags = currentTags;
            vm.message = rejection;
            vm.rejected = true;
            vm.disabled = false;
        });
}

const isFilterable = term => {
    const field = term[0].split('.')[0].replace(/^-/, '');
    return (OUTPUT_SEARCH_FIELDS.indexOf(field) > -1);
};

function removeSearchTag (index) {
    const searchTerm = vm.tags[index];

    const currentQueryset = getCurrentQueryset();
    const modifiedQueryset = qs.removeTermsFromQueryset(currentQueryset, searchTerm, isFilterable);

    reloadQueryset(modifiedQueryset);
}

function submitSearch () {
    // empty input, not submit new search, return.
    if (!vm.value) {
        return;
    }

    const currentQueryset = getCurrentQueryset();
    // check duplicate , see if search input already exists in current search tags
    if (currentQueryset.search) {
        if (currentQueryset.search.includes(vm.value)) {
            return;
        }
    }

    const searchInputQueryset = qs.getSearchInputQueryset(vm.value, isFilterable);
    const modifiedQueryset = qs.mergeQueryset(currentQueryset, searchInputQueryset);

    reloadQueryset(modifiedQueryset, strings.get('search.REJECT_INVALID'));
}

function clearSearch () {
    reloadQueryset();
}

function JobSearchController (_$state_, _qs_, _strings_, { subscribe }) {
    $state = _$state_;
    qs = _qs_;
    strings = _strings_;

    vm = this || {};
    vm.strings = strings;

    vm.examples = OUTPUT_SEARCH_KEY_EXAMPLES;
    vm.fields = OUTPUT_SEARCH_FIELDS;
    vm.docLink = OUTPUT_SEARCH_DOCLINK;
    vm.relatedFields = [];

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
        vm.running = false;
        vm.tags = getSearchTags(getCurrentQueryset());

        unsubscribe = subscribe(({ running }) => {
            vm.disabled = running;
            vm.running = running;
        });
    };

    vm.$onDestroy = () => {
        unsubscribe();
    };
}

JobSearchController.$inject = [
    '$state',
    'QuerySet',
    'OutputStrings',
    'OutputStatusService',
];

export default {
    templateUrl,
    controller: JobSearchController,
    controllerAs: 'vm',
    bindings: {
        reload: '=',
    },
};
