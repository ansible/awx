export default ['$stateParams', '$scope', '$state', 'QuerySet', 'GetBasePath', 'QuerySet', 'SmartSearchService',
    function($stateParams, $scope, $state, QuerySet, GetBasePath, qs, SmartSearchService) {

        let path, relations,
            defaults,
            queryset,
            stateChangeSuccessListener;

        if($scope.defaultParams) {
            defaults = $scope.defaultParams;
        }
        else {
            // steps through the current tree of $state configurations, grabs default search params
            defaults = _.find($state.$current.path, (step) => {
                return step.params.hasOwnProperty(`${$scope.iterator}_search`);
            }).params[`${$scope.iterator}_search`].config.value;
        }

        if($scope.querySet) {
            queryset = _.cloneDeep($scope.querySet);
        }
        else {
            queryset = $stateParams[`${$scope.iterator}_search`];
        }

        // build $scope.tags from $stateParams.QuerySet, build fieldset key
        init();

        function init() {
            path = GetBasePath($scope.basePath) || $scope.basePath;
            relations = getRelationshipFields($scope.dataset.results);
            $scope.searchTags = stripDefaultParams($state.params[`${$scope.iterator}_search`]);
            qs.initFieldset(path, $scope.djangoModel, relations).then((data) => {
                $scope.models = data.models;
                $scope.options = data.options.data;
                $scope.$emit(`${$scope.list.iterator}_options`, data.options);
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
                        $scope.searchTags = stripDefaultParams(queryset);
                    }
                }
            });

            $scope.$on('$destroy', stateChangeSuccessListener);
        }

        // Removes state definition defaults and pagination terms
        function stripDefaultParams(params) {
            let stripped =_.pick(params, (value, key) => {
                // setting the default value of a term to null in a state definition is a very explicit way to ensure it will NEVER generate a search tag, even with a non-default value
                return defaults[key] !== value && key !== 'order_by' && key !== 'page' && key !== 'page_size' && defaults[key] !== null;
            });
            let strippedCopy = _.cloneDeep(stripped);
            if(_.keys(_.pick(defaults, _.keys(strippedCopy))).length > 0){
                for (var key in strippedCopy) {
                    if (strippedCopy.hasOwnProperty(key)) {
                        let value = strippedCopy[key];
                        if(_.isArray(value)){
                            let index = _.indexOf(value, defaults[key]);
                            value = value.splice(index, 1)[0];
                        }
                    }
                }
                stripped = strippedCopy;
            }
            return _(strippedCopy).map(qs.decodeParam).flatten().value();
        }

        // searchable relationships
        function getRelationshipFields(dataset) {
            let flat = _(dataset).map((value) => {
                return _.keys(value.related);
            }).flatten().uniq().value();
            return flat;
        }

        function setDefaults(term) {
            if ($scope.list.defaultSearchParams) {
                return $scope.list.defaultSearchParams(term);
            } else {
               return {
                    search: encodeURIComponent(term)
                };
            }
        }

        $scope.toggleKeyPane = function() {
            $scope.showKeyPane = !$scope.showKeyPane;
        };

        $scope.clearAll = function(){
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
            $scope.searchTags = stripDefaultParams(queryset);
        };

        // remove tag, merge new queryset, $state.go
        $scope.remove = function(index) {
            let tagToRemove = $scope.searchTags.splice(index, 1)[0];
            let termParts = SmartSearchService.splitTermIntoParts(tagToRemove);
            let removed;
            if (termParts.length === 1) {
                removed = setDefaults(tagToRemove);
            }
            else {
                let root = termParts[0].split(".")[0].replace(/^-/, '');
                let encodeParams = {
                    term: tagToRemove
                };
                if(_.has($scope.options.actions.GET, root)) {
                    if($scope.options.actions.GET[root].type && $scope.options.actions.GET[root].type === 'field') {
                        encodeParams.relatedSearchTerm = true;
                    }
                    else {
                        encodeParams.searchTerm = true;
                    }
                }
                removed = qs.encodeParam(encodeParams);
            }
            _.each(removed, (value, key) => {
                if (Array.isArray(queryset[key])){
                    _.remove(queryset[key], (item) => item === value);
                    // If the array is now empty, remove that key
                    if(queryset[key].length === 0) {
                        delete queryset[key];
                    }
                }
                else {
                    delete queryset[key];
                }
            });
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
            $scope.searchTags = stripDefaultParams(queryset);
        };

        // add a search tag, merge new queryset, $state.go()
        $scope.add = function(terms) {
            let params = {},
                origQueryset = _.clone(queryset);

            // Remove leading/trailing whitespace if there is any
            terms = terms.trim();

            if(terms && terms !== '') {
                // Split the terms up
                let splitTerms = SmartSearchService.splitSearchIntoTerms(terms);
                _.forEach(splitTerms, (term) => {

                    let termParts = SmartSearchService.splitTermIntoParts(term);

                    function combineSameSearches(a,b){
                        if (_.isArray(a)) {
                          return a.concat(b);
                        }
                        else {
                            if(a) {
                                return [a,b];
                            }
                        }
                    }

                    // if only a value is provided, search using default keys
                    if (termParts.length === 1) {
                        params = _.merge(params, setDefaults(term), combineSameSearches);
                    } else {
                        // Figure out if this is a search term
                        let root = termParts[0].split(".")[0].replace(/^-/, '');
                        if(_.has($scope.options.actions.GET, root)) {
                            if($scope.options.actions.GET[root].type && $scope.options.actions.GET[root].type === 'field') {
                                params = _.merge(params, qs.encodeParam({term: term, relatedSearchTerm: true}), combineSameSearches);
                            }
                            else {
                                params = _.merge(params, qs.encodeParam({term: term, searchTerm: true}), combineSameSearches);
                            }
                        }
                        // Its not a search term or a related search term - treat it as a string
                        else {
                            params = _.merge(params, setDefaults(term), combineSameSearches);
                        }

                    }
                });

                params.page = '1';
                queryset = _.merge(queryset, params, (objectValue, sourceValue, key, object) => {
                    if (object[key] && object[key] !== sourceValue){
                        if(_.isArray(object[key])) {
                            // Add the new value to the array and return
                            object[key].push(sourceValue);
                            return object[key];
                        }
                        else {
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
                })
                .catch(function() {
                    $scope.revertSearch(origQueryset);
                });

                $scope.searchTerm = null;
                $scope.searchTags = stripDefaultParams(queryset);
            }
        };

        $scope.revertSearch = function(queryToBeRestored) {
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
            $scope.searchTags = stripDefaultParams(queryset);
        };
    }
];
