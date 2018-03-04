function SmartSearchController (
    $scope,
    $state,
    $stateParams,
    $transitions,
    configService,
    GetBasePath,
    i18n,
    qs,
    SmartSearchService
) {
    const searchKey = `${$scope.iterator}_search`;
    const optionsKey = `${$scope.list.iterator}_options`;

    let path;
    let defaults;
    let queryset;
    let transitionSuccessListener;

    configService.getConfig()
        .then(config => init(config));

    function init (config) {
        let version;

        try {
            [version] = config.version.split('-');
        } catch (err) {
            version = 'latest';
        }

        $scope.documentationLink = `http://docs.ansible.com/ansible-tower/${version}/html/userguide/search_sort.html`;
        $scope.searchPlaceholder = i18n._('Search');

        if ($scope.defaultParams) {
            defaults = $scope.defaultParams;
        } else {
            // steps through the current tree of $state configurations, grabs default search params
            const stateConfig = _.find($state.$current.path, step => _.has(step, `params.${searchKey}`));
            defaults = stateConfig.params[searchKey].config.value;
        }

        if ($scope.querySet) {
            queryset = _.cloneDeep($scope.querySet);
        } else {
            queryset = $state.params[searchKey];
        }

        path = GetBasePath($scope.basePath) || $scope.basePath;
        generateSearchTags();

        qs.initFieldset(path, $scope.djangoModel)
            .then((data) => {
                $scope.models = data.models;
                $scope.options = data.options.data;
                if ($scope.list) {
                    $scope.$emit(optionsKey, data.options);
                }
            });

        function compareParams(a, b) {
            for (let key in a) {
                if (!(key in b) || a[key].toString() !== b[key].toString()) {
                    return false;
                }
            }
            for (let key in b) {
                if (!(key in a)) {
                    return false;
                }
            }
            return true;
        }

        if (transitionSuccessListener) {
            transitionSuccessListener();
        }

        transitionSuccessListener = $transitions.onSuccess({}, trans => {
            // State has changed - check to see if this is a param change
            if (trans.from().name === trans.to().name) {
                if (!compareParams(trans.params('from')[searchKey], trans.params('to')[searchKey])) {
                    // Params are not the same - we need to update the search. This should only
                    // happen when the user hits the forward/back browser navigation buttons.
                    queryset = trans.params('to')[searchKey];
                    qs.search(path, queryset).then((res) => {
                        $scope.dataset = res.data;
                        $scope.collection = res.data.results;
                        $scope.$emit('updateDataset', res.data);
                    });

                    $scope.searchTerm = null;
                    generateSearchTags();
                }
            }
        });

        $scope.$on('$destroy', transitionSuccessListener);
        $scope.$watch('disableSearch', disableSearch => {
            if (disableSearch) {
                $scope.searchPlaceholder = i18n._('Cannot search running job');
            } else {
                $scope.searchPlaceholder = i18n._('Search');
            }
        });
    }

    function generateSearchTags () {
        $scope.searchTags = [];

        const querysetCopy = angular.copy(queryset);

        if ($scope.singleSearchParam && querysetCopy[$scope.singleSearchParam]) {
            const searchParam = querysetCopy[$scope.singleSearchParam].split('%20and%20');
            delete querysetCopy[$scope.singleSearchParam];

            $.each(searchParam, (index, param) => {
                const paramParts = decodeURIComponent(param).split(/=(.+)/);
                const reconstructedSearchString = qs.decodeParam(paramParts[1], paramParts[0]);
                $scope.searchTags.push(reconstructedSearchString);
            });
        }

        $scope.searchTags = $scope.searchTags.concat(qs.stripDefaultParams(querysetCopy, defaults));
    }

    function revertSearch (queryToBeRestored) {
        queryset = queryToBeRestored;
        // https://ui-router.github.io/docs/latest/interfaces/params.paramdeclaration.html#dynamic
        // This transition will not reload controllers/resolves/views
        // but will register new $stateParams[$scope.iterator + '_search'] terms
        if (!$scope.querySet) {
            $state.go('.', { [searchKey]: queryset });
        }
        qs.search(path, queryset).then((res) => {
            if ($scope.querySet) {
                $scope.querySet = queryset;
            }
            $scope.dataset = res.data;
            $scope.collection = res.data.results;
        });

        $scope.searchTerm = null;

        generateSearchTags();
    }

    $scope.toggleKeyPane = () => {
        $scope.showKeyPane = !$scope.showKeyPane;
    };

    function searchWithoutKey (term, singleSearchParam = null) {
        if (singleSearchParam) {
            return { [singleSearchParam]: `search=${encodeURIComponent(term)}` };
        }
        return { search: encodeURIComponent(term) };
    }

    function isAnsibleFactSearchTerm (termParts) {
        const rootField = termParts[0].split('.')[0].replace(/^-/, '');
        return rootField === 'ansible_facts';
    }

    function isRelatedField (termParts) {
        const rootField = termParts[0].split('.')[0].replace(/^-/, '');
        const listName = $scope.list.name;
        const baseRelatedTypePath = `models.${listName}.base.${rootField}.type`;

        const isRelatedSearchTermField = (_.contains($scope.models[listName].related, rootField));
        const isBaseModelRelatedSearchTermField = (_.get($scope, baseRelatedTypePath) === 'field');

        return (isRelatedSearchTermField || isBaseModelRelatedSearchTermField);
    }

    function getSearchInputQueryset ({ terms, singleSearchParam }) {
        let params = {};

        // remove leading/trailing whitespace
        terms = (terms) ? terms.trim() : '';
        let splitTerms;

        if (singleSearchParam === 'host_filter') {
            splitTerms = SmartSearchService.splitFilterIntoTerms(terms);
        } else {
            splitTerms = SmartSearchService.splitSearchIntoTerms(terms);
        }

        const combineSameSearches = (a, b) => {
            if (!a) {
                return undefined;
            }

            if (_.isArray(a)) {
                return a.concat(b);
            }

            if (singleSearchParam) {
                return `${a}%20and%20${b}`;
            }

            return [a, b];
        };

        _.each(splitTerms, term => {
            const termParts = SmartSearchService.splitTermIntoParts(term);
            let termParams;

            if (termParts.length === 1) {
                termParams = searchWithoutKey(term, singleSearchParam);
            } else if (isAnsibleFactSearchTerm(termParts)) {
                termParams = qs.encodeParam({ term, singleSearchParam });
            } else if (isRelatedField(termParts)) {
                termParams = qs.encodeParam({ term, singleSearchParam, related: true });
            } else {
                termParams = qs.encodeParam({ term, singleSearchParam });
            }

            params = _.merge(params, termParams, combineSameSearches);
        });

        return params;
    }

    function mergeQueryset (qset, additional, singleSearchParam) {
        const merged = _.merge({}, qset, additional, (objectValue, sourceValue, key, object) => {
            if (!(object[key] && object[key] !== sourceValue)) {
                // // https://lodash.com/docs/3.10.1#each
                // If this returns undefined merging is handled by default _.merge algorithm
                return undefined;
            }

            if (_.isArray(object[key])) {
                object[key].push(sourceValue);
                return object[key];
            }

            if (singleSearchParam) {
                if (!object[key]) {
                    return sourceValue;
                }

                const singleSearchParamKeys = object[key].split('%20and%20');

                if (_.includes(singleSearchParamKeys, sourceValue)) {
                    return object[key];
                }

                return `${object[key]}%20and%20${sourceValue}`;
            }

            // Start the array of keys
            return [object[key], sourceValue];
        });

        return merged;
    }

    $scope.addTerms = terms => {
        const { singleSearchParam } = $scope;
        const origQueryset = _.clone(queryset);

        // Remove leading/trailing whitespace if there is any
        terms = (terms) ? terms.trim() : '';

        if (!(terms && terms !== '')) {
            return;
        }

        const searchInputQueryset = getSearchInputQueryset({ terms, singleSearchParam });
        queryset = mergeQueryset(queryset, searchInputQueryset, singleSearchParam);

        // Go back to the first page after a new search
        delete queryset.page;

        // https://ui-router.github.io/docs/latest/interfaces/params.paramdeclaration.html#dynamic
        // This transition will not reload controllers/resolves/views but will register new
        // $stateParams[searchKey] terms.
        if (!$scope.querySet) {
            $state.go('.', { [searchKey]: queryset })
                .then(() => {
                    // same as above in $scope.remove.  For some reason deleting the page
                    // from the queryset works for all lists except lists in modals.
                    delete $stateParams[searchKey].page;
                });
        }

        qs.search(path, queryset)
            .then(({ data }) => {
                if ($scope.querySet) {
                    $scope.querySet = queryset;
                }
                $scope.dataset = data;
                $scope.collection = data.results;
            })
            .catch(() => revertSearch(origQueryset));

        $scope.searchTerm = null;

        generateSearchTags();
    };

    function removeTermsFromQueryset(qset, term, singleSearchParam = null) {
        const returnedQueryset = _.cloneDeep(qset);

        const removeSingleTermFromQueryset = (value, key) => {
            const space = '%20and%20';

            if (Array.isArray(returnedQueryset[key])) {
                returnedQueryset[key] = returnedQueryset[key].filter(item => item !== value);
                if (returnedQueryset[key].length < 1) {
                    delete returnedQueryset[key];
                }
            } else if (singleSearchParam && _.get(returnedQueryset, singleSearchParam, []).includes(space)) {
                const searchParamParts = returnedQueryset[singleSearchParam].split(space);
                // The value side of each paramPart might have been encoded in
                // SmartSearch.splitFilterIntoTerms
                _.each(searchParamParts, (paramPart, paramPartIndex) => {
                    searchParamParts[paramPartIndex] = decodeURIComponent(paramPart);
                });

                const paramPartIndex = searchParamParts.indexOf(value);

                if (paramPartIndex !== -1) {
                    searchParamParts.splice(paramPartIndex, 1);
                }

                returnedQueryset[singleSearchParam] = searchParamParts.join(space);

            } else {
                delete returnedQueryset[key];
            }
        };

        const termParts = SmartSearchService.splitTermIntoParts(term);

        let removed;

        if (termParts.length === 1) {
            removed = searchWithoutKey(term, singleSearchParam);
        } else if (isRelatedField(termParts)) {
            removed = qs.encodeParam({ term, singleSearchParam, related: true });
        } else {
            removed = qs.encodeParam({ term, singleSearchParam });
        }

        if (!removed) {
            removed = searchWithoutKey(termParts[termParts.length - 1], singleSearchParam);
        }

        _.each(removed, removeSingleTermFromQueryset);

        return returnedQueryset;
    }

    // remove tag, merge new queryset, $state.go
    $scope.removeTerm = index => {
        const { singleSearchParam } = $scope;
        const [term] = $scope.searchTags.splice(index, 1);

        const modifiedQueryset = removeTermsFromQueryset(queryset, term, singleSearchParam);

        if (!$scope.querySet) {
            $state.go('.', { [searchKey]: modifiedQueryset })
                .then(() => {
                    // for some reason deleting a tag from a list in a modal does not
                    // remove the param from $stateParams.  Here we'll manually check to make sure
                    // that that happened and remove it if it didn't.
                    const clearedParams = removeTermsFromQueryset(
                        $stateParams[searchKey], term, singleSearchParam);
                    $stateParams[searchKey] = clearedParams;
                });
        }

        qs.search(path, queryset)
            .then(({ data }) => {
                if ($scope.querySet) {
                    $scope.querySet = queryset;
                }
                $scope.dataset = data;
                $scope.collection = data.results;
            });

        generateSearchTags();
    };

    $scope.clearAllTerms = () => {
        const cleared = _.cloneDeep(defaults);

        delete cleared.page;

        queryset = cleared;

        if (!$scope.querySet) {
            $state.go('.', { [searchKey]: queryset });
        }

        qs.search(path, queryset)
            .then(({ data }) => {
                if ($scope.querySet) {
                    $scope.querySet = queryset;
                }
                $scope.dataset = data;
                $scope.collection = data.results;
            });

        $scope.searchTags = qs.stripDefaultParams(queryset, defaults);
    };
}

SmartSearchController.$inject = [
    '$scope',
    '$state',
    '$stateParams',
    '$transitions',
    'ConfigService',
    'GetBasePath',
    'i18n',
    'QuerySet',
    'SmartSearchService',
];

export default SmartSearchController;
