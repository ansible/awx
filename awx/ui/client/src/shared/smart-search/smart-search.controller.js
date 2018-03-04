function SmartSearchController (
    $scope,
    $state,
    $stateParams,
    $transitions,
    configService,
    GetBasePath,
    i18n,
    qs,
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

        function compareParams (a, b) {
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
        const { singleSearchParam } = $scope;
        $scope.searchTags = qs.createSearchTagsFromQueryset(queryset, defaults, singleSearchParam);
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

    function isAnsibleFactField (termParts) {
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

    $scope.addTerms = terms => {
        const { singleSearchParam } = $scope;
        const unmodifiedQueryset = _.clone(queryset);

        const searchInputQueryset = qs.getSearchInputQueryset(terms, isRelatedField, isAnsibleFactField, singleSearchParam);
        const modifiedQueryset = qs.mergeQueryset(queryset, searchInputQueryset, singleSearchParam);

        // Go back to the first page after a new search
        delete modifiedQueryset.page;

        // https://ui-router.github.io/docs/latest/interfaces/params.paramdeclaration.html#dynamic
        // This transition will not reload controllers/resolves/views but will register new
        // $stateParams[searchKey] terms.
        if (!$scope.querySet) {
            $state.go('.', { [searchKey]: modifiedQueryset })
                .then(() => {
                    // same as above in $scope.remove.  For some reason deleting the page
                    // from the queryset works for all lists except lists in modals.
                    delete $stateParams[searchKey].page;
                });
        }

        qs.search(path, modifiedQueryset)
            .then(({ data }) => {
                if ($scope.querySet) {
                    $scope.querySet = modifiedQueryset;
                }
                $scope.dataset = data;
                $scope.collection = data.results;
            })
            .catch(() => revertSearch(unmodifiedQueryset));

        $scope.searchTerm = null;

        generateSearchTags();
    };
    // remove tag, merge new queryset, $state.go
    $scope.removeTerm = index => {
        const { singleSearchParam } = $scope;
        const [term] = $scope.searchTags.splice(index, 1);

        const modifiedQueryset = qs.removeTermsFromQueryset(queryset, term, isRelatedField, singleSearchParam);

        if (!$scope.querySet) {
            $state.go('.', { [searchKey]: modifiedQueryset })
                .then(() => {
                    // for some reason deleting a tag from a list in a modal does not
                    // remove the param from $stateParams.  Here we'll manually check to make sure
                    // that that happened and remove it if it didn't.
                    const clearedParams = qs.removeTermsFromQueryset($stateParams[searchKey], term, isRelatedField, singleSearchParam);
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
];

export default SmartSearchController;
