function SmartSearchController (
    $scope,
    $rootScope,
    $state,
    $stateParams,
    $transitions,
    configService,
    GetBasePath,
    i18n,
    qs
) {
    const searchKey = `${$scope.iterator}_search`;
    const optionsKey = `${$scope.list.iterator}_options`;

    let path;
    let defaults;
    let queryset;
    let transitionSuccessListener;

    const compareParams = (a, b) => {
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
    };

    const generateSearchTags = () => {
        const { singleSearchParam } = $scope;
        $scope.searchTags = qs.createSearchTagsFromQueryset(queryset, defaults, singleSearchParam);
    };

    const listenForTransitionSuccess = () => {
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
                        $scope.$emit('updateDataset', res.data, queryset);
                    });

                    $scope.searchTerm = null;
                    generateSearchTags();
                }
            }
        });
    };

    const isAnsibleFactField = (termParts) => {
        const rootField = termParts[0].split('.')[0].replace(/^-/, '');
        return rootField === 'ansible_facts';
    };

    const revertSearch = (queryToBeRestored) => {
        queryset = queryToBeRestored;
        // https://ui-router.github.io/docs/latest/interfaces/params.paramdeclaration.html#dynamic
        // This transition will not reload controllers/resolves/views
        // but will register new $stateParams[$scope.iterator + '_search'] terms
        if (!$scope.querySet) {
            transitionSuccessListener();
            $state.go('.', { [searchKey]: queryset })
            .then(() => listenForTransitionSuccess());
        }
        qs.search(path, queryset).then((res) => {
            if ($scope.querySet) {
                $scope.querySet = queryset;
            }
            $scope.dataset = res.data;
            $scope.collection = res.data.results;
            $scope.$emit('updateDataset', res.data, queryset);
        });

        $scope.searchTerm = null;

        generateSearchTags();
    };

    const isFilterableBaseField = (termParts) => {
        const rootField = termParts[0].split('.')[0].replace(/^-/, '');
        const listName = $scope.list.name;
        const baseFieldPath = `models.${listName}.base.${rootField}`;
        const isBaseField = _.has($scope, `${baseFieldPath}`);

        const isFilterable = _.get($scope, `${baseFieldPath}.filterable`);
        const isBaseModelRelatedSearchTermField = (_.get($scope, `${baseFieldPath}.type`) === 'field');

        return isBaseField && !isBaseModelRelatedSearchTermField && isFilterable;
    };

    const isRelatedField = (termParts) => {
        const rootField = termParts[0].split('.')[0].replace(/^-/, '');
        const listName = $scope.list.name;
        const baseRelatedTypePath = `models.${listName}.base.${rootField}.type`;
        const relatedTypePath = `models.${listName}.related`;

        const isRelatedSearchTermField = (_.includes(_.get($scope, relatedTypePath), rootField));
        const isBaseModelRelatedSearchTermField = (_.get($scope, baseRelatedTypePath) === 'field');

        return (isRelatedSearchTermField || isBaseModelRelatedSearchTermField);
    };

    configService.getConfig()
        .then(config => {
            let version;
            if ($rootScope.BRAND_NAME === 'Tower') {
                try {
                    [version] = config.version.split('-');
                } catch (err) {
                    version = 'latest';
                }
            } else {
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
                queryset = $scope.querySet;
            } else {
                queryset = $state.params[searchKey];
            }

            path = GetBasePath($scope.basePath) || $scope.basePath;
            generateSearchTags();

            qs.initFieldset(path, $scope.djangoModel)
                .then((data) => {
                    $scope.models = data.models;
                    $scope.options = data.options.data;
                    $scope.keyFields = _.reduce(data.models[$scope.djangoModel].base, (result, value, key) => {
                        if (value.filterable) {
                            result.push(key);
                        }
                        return result;
                    }, []);
                    if ($scope.list) {
                        $scope.$emit(optionsKey, data.options);
                    }
                });
            $scope.$on('$destroy', () => {
                if (transitionSuccessListener) {
                    transitionSuccessListener();
                }
            });
            $scope.$watch('disableSearch', disableSearch => {
                if (disableSearch) {
                    $scope.searchPlaceholder = i18n._('Cannot search running job');
                } else {
                    $scope.searchPlaceholder = i18n._('Search');
                }
            });
            listenForTransitionSuccess();
        });


    $scope.toggleKeyPane = () => {
        $scope.showKeyPane = !$scope.showKeyPane;
    };

    $scope.addTerms = terms => {
        if (terms && terms !== "") {
            const { singleSearchParam } = $scope;
            const unmodifiedQueryset = _.clone(queryset);

            const searchInputQueryset = qs.getSearchInputQueryset(terms, isFilterableBaseField, isRelatedField, isAnsibleFactField, singleSearchParam);
            queryset = qs.mergeQueryset(queryset, searchInputQueryset, singleSearchParam);

            // Go back to the first page after a new search
            delete queryset.page;

            // https://ui-router.github.io/docs/latest/interfaces/params.paramdeclaration.html#dynamic
            // This transition will not reload controllers/resolves/views but will register new
            // $stateParams[searchKey] terms.
            if (!$scope.querySet) {
                transitionSuccessListener();
                $state.go('.', { [searchKey]: queryset })
                    .then(() => {
                        // same as above in $scope.remove.  For some reason deleting the page
                        // from the queryset works for all lists except lists in modals.
                        delete $stateParams[searchKey].page;
                        listenForTransitionSuccess();
                    });
            }

            qs.search(path, queryset, singleSearchParam)
                .then(({ data }) => {
                    if ($scope.querySet) {
                        $scope.querySet = queryset;
                    }
                    $scope.dataset = data;
                    $scope.collection = data.results;
                    $scope.$emit('updateDataset', data, queryset);
                })
                .catch(() => revertSearch(unmodifiedQueryset));

            $scope.searchTerm = null;

            generateSearchTags();
        }
    };
    // remove tag, merge new queryset, $state.go
    $scope.removeTerm = index => {
        const { singleSearchParam } = $scope;
        const [term] = $scope.searchTags.splice(index, 1);

        queryset = qs.removeTermsFromQueryset(queryset, term, isFilterableBaseField, isRelatedField, isAnsibleFactField, singleSearchParam);

        if (!$scope.querySet) {
            transitionSuccessListener();
            $state.go('.', { [searchKey]: queryset })
                .then(() => {
                    // for some reason deleting a tag from a list in a modal does not
                    // remove the param from $stateParams.  Here we'll manually check to make sure
                    // that that happened and remove it if it didn't.
                    const clearedParams = qs.removeTermsFromQueryset($stateParams[searchKey], term, isFilterableBaseField, isRelatedField, isAnsibleFactField, singleSearchParam);
                    $stateParams[searchKey] = clearedParams;
                    listenForTransitionSuccess();
                });
        }

        qs.search(path, queryset)
            .then(({ data }) => {
                if ($scope.querySet) {
                    $scope.querySet = queryset;
                }
                $scope.dataset = data;
                $scope.collection = data.results;
                $scope.$emit('updateDataset', data, queryset);
            });

        generateSearchTags();
    };

    $scope.clearAllTerms = () => {
        _.forOwn(defaults, (value, key) => {
            // preserve the `credential_type` queryset param if it exists
            if (key === 'credential_type') {
                defaults[key] = queryset[key];
            }
        });
        const cleared = _(defaults).omitBy(_.isNull).value();
        delete cleared.page;
        queryset = cleared;

        if (!$scope.querySet) {
            transitionSuccessListener();
            $state.go('.', { [searchKey]: queryset })
            .then(() => listenForTransitionSuccess());
        }

        qs.search(path, queryset)
            .then(({ data }) => {
                if ($scope.querySet) {
                    $scope.querySet = queryset;
                }
                $scope.dataset = data;
                $scope.collection = data.results;
                $scope.$emit('updateDataset', data, queryset);
            });

        $scope.searchTags = qs.stripDefaultParams(queryset, defaults);
    };
}

SmartSearchController.$inject = [
    '$scope',
    '$rootScope',
    '$state',
    '$stateParams',
    '$transitions',
    'ConfigService',
    'GetBasePath',
    'i18n',
    'QuerySet',
];

export default SmartSearchController;
