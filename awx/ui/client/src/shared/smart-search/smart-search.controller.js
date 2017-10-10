export default ['$stateParams', '$scope', '$state', 'GetBasePath', 'QuerySet', 'SmartSearchService', 'i18n', 'ConfigService',
    function($stateParams, $scope, $state, GetBasePath, qs, SmartSearchService, i18n, configService) {

        let path,
            defaults,
            queryset,
            stateChangeSuccessListener;

        configService.getConfig()
            .then(config => init(config));

        function init(config) {
            let version;

            try {
                version = config.version.split('-')[0];
            } catch (err) {
                version = 'latest';
            }

            $scope.documentationLink =  `http://docs.ansible.com/ansible-tower/${version}/html/userguide/search_sort.html`;

            if($scope.defaultParams) {
                defaults = $scope.defaultParams;
            }
            else {
                // steps through the current tree of $state configurations, grabs default search params
                defaults = _.find($state.$current.path, (step) => {
                    if(step && step.params && step.params.hasOwnProperty(`${$scope.iterator}_search`)){
                        return step.params.hasOwnProperty(`${$scope.iterator}_search`);
                    }
                }).params[`${$scope.iterator}_search`].config.value;
            }

            if($scope.querySet) {
                queryset = _.cloneDeep($scope.querySet);
            }
            else {
                queryset = $state.params[`${$scope.iterator}_search`];
            }

            path = GetBasePath($scope.basePath) || $scope.basePath;
            generateSearchTags();
            qs.initFieldset(path, $scope.djangoModel).then((data) => {
                $scope.models = data.models;
                $scope.options = data.options.data;
                $scope.$emit(`${$scope.list.iterator}_options`, data.options);
            });
            $scope.searchPlaceholder = $scope.disableSearch ? i18n._('Cannot search running job') : i18n._('Search');

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

            if(stateChangeSuccessListener) {
                stateChangeSuccessListener();
            }

            stateChangeSuccessListener = $scope.$on('$stateChangeSuccess', function(event, toState, toParams, fromState, fromParams) {
                // State has changed - check to see if this is a param change
                if(fromState.name === toState.name) {
                    if(!compareParams(fromParams[`${$scope.iterator}_search`], toParams[`${$scope.iterator}_search`])) {
                        // Params are not the same - we need to update the search.  This should only happen when the user
                        // hits the forward/back navigation buttons in their browser.
                        queryset = toParams[`${$scope.iterator}_search`];
                        qs.search(path, queryset).then((res) => {
                            $scope.dataset = res.data;
                            $scope.collection = res.data.results;
                        });

                        $scope.searchTerm = null;
                        generateSearchTags();
                    }
                }
            });

            $scope.$on('$destroy', stateChangeSuccessListener);

            $scope.$watch('disableSearch', function(disableSearch){
                if(disableSearch) {
                    $scope.searchPlaceholder = i18n._('Cannot search running job');
                }
                else {
                    $scope.searchPlaceholder = i18n._('Search');
                }
            });
        }

        function generateSearchTags() {
            $scope.searchTags = [];

            let querysetCopy = angular.copy(queryset);

            if($scope.singleSearchParam && querysetCopy[$scope.singleSearchParam]) {
                let searchParam = querysetCopy[$scope.singleSearchParam].split('%20and%20');
                delete querysetCopy[$scope.singleSearchParam];

                $.each(searchParam, function(index, param) {
                    let paramParts = decodeURIComponent(param).split(/=(.+)/);
                    let reconstructedSearchString = qs.decodeParam(paramParts[1], paramParts[0]);
                    $scope.searchTags.push(reconstructedSearchString);
                });
            }

            $scope.searchTags = $scope.searchTags.concat(qs.stripDefaultParams(querysetCopy, defaults));
        }

        function revertSearch(queryToBeRestored) {
            queryset = queryToBeRestored;
            // https://ui-router.github.io/docs/latest/interfaces/params.paramdeclaration.html#dynamic
            // This transition will not reload controllers/resolves/views
            // but will register new $stateParams[$scope.iterator + '_search'] terms
            if(!$scope.querySet) {
                $state.go('.', {
                    [$scope.iterator + '_search']: queryset }, {notify: false});
            }
            qs.search(path, queryset).then((res) => {
                if($scope.querySet) {
                    $scope.querySet = queryset;
                }
                $scope.dataset = res.data;
                $scope.collection = res.data.results;
            });

            $scope.searchTerm = null;

            generateSearchTags();
        }

        function searchWithoutKey(term) {
            if($scope.singleSearchParam) {
                return {
                    [$scope.singleSearchParam]: encodeURIComponent("search=" + term)
                };
            }
           return {
                search: encodeURIComponent(term)
            };
        }

        $scope.toggleKeyPane = function() {
            $scope.showKeyPane = !$scope.showKeyPane;
        };

        // add a search tag, merge new queryset, $state.go()
        $scope.addTerm = function(terms) {
            let params = {},
                origQueryset = _.clone(queryset);

            // Remove leading/trailing whitespace if there is any
            terms = (terms) ? terms.trim() : "";

            if(terms && terms !== '') {
                let splitTerms;

                if ($scope.singleSearchParam === 'host_filter') {
                    splitTerms = SmartSearchService.splitFilterIntoTerms(terms);
                } else {
                    splitTerms = SmartSearchService.splitSearchIntoTerms(terms);
                }

                _.forEach(splitTerms, (term) => {
                    let termParts = SmartSearchService.splitTermIntoParts(term);

                    function combineSameSearches(a,b){
                        if (_.isArray(a)) {
                          return a.concat(b);
                        }
                        else {
                            if(a) {
                                if($scope.singleSearchParam) {
                                    return a + "%20and%20" + b;
                                }
                                else {
                                    return [a,b];
                                }
                            }
                        }
                    }

                    if($scope.singleSearchParam) {
                        if (termParts.length === 1) {
                            params = _.merge(params, searchWithoutKey(term), combineSameSearches);
                        }
                        else {
                            let root = termParts[0].split(".")[0].replace(/^-/, '');
                            if(_.has($scope.models[$scope.list.name].base, root) || root === "ansible_facts") {
                                if(_.has($scope.models[$scope.list.name].base[root], "type") && $scope.models[$scope.list.name].base[root].type === 'field'){
                                    // Intent is to land here for searching on the base model.
                                    params = _.merge(params, qs.encodeParam({term: term, relatedSearchTerm: true, singleSearchParam: $scope.singleSearchParam ? $scope.singleSearchParam : false}), combineSameSearches);
                                }
                                else {
                                    // Intent is to land here when performing ansible_facts searches
                                    params = _.merge(params, qs.encodeParam({term: term, searchTerm: true, singleSearchParam: $scope.singleSearchParam ? $scope.singleSearchParam : false}), combineSameSearches);
                                }
                            }
                            else if(_.contains($scope.models[$scope.list.name].related, root)) {
                                // Intent is to land here for related searches
                                params = _.merge(params, qs.encodeParam({term: term, relatedSearchTerm: true, singleSearchParam: $scope.singleSearchParam ? $scope.singleSearchParam : false}), combineSameSearches);
                            }
                            // Its not a search term or a related search term - treat it as a string
                            else {
                                params = _.merge(params, searchWithoutKey(term), combineSameSearches);
                            }
                        }
                    }

                    else {
                        // if only a value is provided, search using default keys
                        if (termParts.length === 1) {
                            params = _.merge(params, searchWithoutKey(term), combineSameSearches);
                        } else {
                            // Figure out if this is a search term
                            let root = termParts[0].split(".")[0].replace(/^-/, '');
                            if(_.has($scope.models[$scope.list.name].base, root)) {
                                if($scope.models[$scope.list.name].base[root].type && $scope.models[$scope.list.name].base[root].type === 'field') {
                                    params = _.merge(params, qs.encodeParam({term: term, relatedSearchTerm: true}), combineSameSearches);
                                }
                                else {
                                    params = _.merge(params, qs.encodeParam({term: term, searchTerm: true}), combineSameSearches);
                                }
                            }
                            // The related fields need to also be checked for related searches.
                            // The related fields for the search are retrieved from the API
                            // options endpoint, and are stored in the $scope.model. FYI, the
                            // Django search model is what sets the related fields on the model.
                            else if(_.contains($scope.models[$scope.list.name].related, root)) {
                                params = _.merge(params, qs.encodeParam({term: term, relatedSearchTerm: true}), combineSameSearches);
                            }
                            // Its not a search term or a related search term - treat it as a string
                            else {
                                params = _.merge(params, searchWithoutKey(term), combineSameSearches);
                            }

                        }
                    }
                });

                queryset = _.merge(queryset, params, (objectValue, sourceValue, key, object) => {
                    if (object[key] && object[key] !== sourceValue){
                        if(_.isArray(object[key])) {
                            // Add the new value to the array and return
                            object[key].push(sourceValue);
                            return object[key];
                        }
                        else {
                            if($scope.singleSearchParam) {
                                if(!object[key]) {
                                    return sourceValue;
                                }
                                else {
                                    let singleSearchParamKeys = object[key].split("%20and%20");

                                    if(_.includes(singleSearchParamKeys, sourceValue)) {
                                        return object[key];
                                    }
                                    else {
                                        return object[key] + "%20and%20" + sourceValue;
                                    }
                                }
                            }
                            // Start the array of keys
                            return [object[key], sourceValue];
                        }
                    }
                    else {
                        // // https://lodash.com/docs/3.10.1#merge
                        // If customizer fn returns undefined merging is handled by default _.merge algorithm
                        return undefined;
                    }
                });

                // Go back to the first page after a new search
                delete queryset.page;

                // https://ui-router.github.io/docs/latest/interfaces/params.paramdeclaration.html#dynamic
                // This transition will not reload controllers/resolves/views
                // but will register new $stateParams[$scope.iterator + '_search'] terms
                if(!$scope.querySet) {
                    $state.go('.', {
                        [$scope.iterator + '_search']: queryset }, {notify: false}).then(function(){
                            // ISSUE: same as above in $scope.remove.  For some reason deleting the page
                            // from the queryset works for all lists except lists in modals.
                            delete $stateParams[$scope.iterator + '_search'].page;
                        });
                }
                qs.search(path, queryset).then((res) => {
                    if($scope.querySet) {
                        $scope.querySet = queryset;
                    }
                    $scope.dataset = res.data;
                    $scope.collection = res.data.results;
                })
                .catch(function() {
                    revertSearch(origQueryset);
                });

                $scope.searchTerm = null;

                generateSearchTags();
            }
        };

        // remove tag, merge new queryset, $state.go
        $scope.removeTerm = function(index) {
            let tagToRemove = $scope.searchTags.splice(index, 1)[0],
                termParts = SmartSearchService.splitTermIntoParts(tagToRemove),
                removed;

            let removeFromQuerySet = function(set) {
                _.each(removed, (value, key) => {
                    if (Array.isArray(set[key])){
                        _.remove(set[key], (item) => item === value);
                        // If the array is now empty, remove that key
                        if(set[key].length === 0) {
                            delete set[key];
                        }
                    }
                    else {
                        if($scope.singleSearchParam && set[$scope.singleSearchParam] && set[$scope.singleSearchParam].includes("%20and%20")) {
                            let searchParamParts = set[$scope.singleSearchParam].split("%20and%20");
                            var index = searchParamParts.indexOf(value);
                            if (index !== -1) {
                                searchParamParts.splice(index, 1);
                            }
                            set[$scope.singleSearchParam] = searchParamParts.join("%20and%20");
                        }
                        else {
                            delete set[key];
                        }
                    }
                });
            };

            if (termParts.length === 1) {
                removed = searchWithoutKey(tagToRemove);
            }
            else {
                let root = termParts[0].split(".")[0].replace(/^-/, '');
                let encodeParams = {
                    term: tagToRemove,
                    singleSearchParam: $scope.singleSearchParam ? $scope.singleSearchParam : false
                };
                if($scope.models[$scope.list.name]) {
                    if($scope.singleSearchParam) {
                        removed = qs.encodeParam(encodeParams);
                    }
                    else if(_.has($scope.models[$scope.list.name].base, root)) {
                        if($scope.models[$scope.list.name].base[root].type && $scope.models[$scope.list.name].base[root].type === 'field') {
                            encodeParams.relatedSearchTerm = true;
                        }
                        else {
                            encodeParams.searchTerm = true;
                        }
                        removed = qs.encodeParam(encodeParams);
                    }
                    else if(_.contains($scope.models[$scope.list.name].related, root)) {
                        encodeParams.relatedSearchTerm = true;
                        removed = qs.encodeParam(encodeParams);
                    }
                    else {
                        removed = searchWithoutKey(termParts[termParts.length-1]);
                    }
                }
                else {
                    removed = searchWithoutKey(termParts[termParts.length-1]);
                }
            }
            removeFromQuerySet(queryset);
            if(!$scope.querySet) {
                $state.go('.', {
                    [$scope.iterator + '_search']: queryset }, {notify: false}).then(function(){
                        // ISSUE: for some reason deleting a tag from a list in a modal does not
                        // remove the param from $stateParams.  Here we'll manually check to make sure
                        // that that happened and remove it if it didn't.

                        removeFromQuerySet($stateParams[`${$scope.iterator}_search`]);
                    });
            }
            qs.search(path, queryset).then((res) => {
                if($scope.querySet) {
                    $scope.querySet = queryset;
                }
                $scope.dataset = res.data;
                $scope.collection = res.data.results;
            });

            generateSearchTags();
        };

        $scope.clearAllTerms = function(){
            let cleared = _.cloneDeep(defaults);
            delete cleared.page;
            queryset = cleared;
            if(!$scope.querySet) {
                $state.go('.', {[$scope.iterator + '_search']: queryset}, {notify: false});
            }
            qs.search(path, queryset).then((res) => {
                if($scope.querySet) {
                    $scope.querySet = queryset;
                }
                $scope.dataset = res.data;
                $scope.collection = res.data.results;
            });
            $scope.searchTags = qs.stripDefaultParams(queryset, defaults);
        };
    }
];
