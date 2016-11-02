export default ['$stateParams', '$scope', '$state', 'QuerySet', 'GetBasePath', 'QuerySet',
    function($stateParams, $scope, $state, QuerySet, GetBasePath, qs) {

        let path, relations,
            // steps through the current tree of $state configurations, grabs default search params
            defaults = _.find($state.$current.path, (step) => {
                return step.params.hasOwnProperty(`${$scope.iterator}_search`);
            }).params[`${$scope.iterator}_search`].config.value,
            queryset = $stateParams[`${$scope.iterator}_search`];

        // build $scope.tags from $stateParams.QuerySet, build fieldset key
        init();

        function init() {
            path = GetBasePath($scope.basePath) || $scope.basePath;
            relations = getRelationshipFields($scope.dataset.results);
            $scope.searchTags = stripDefaultParams($state.params[`${$scope.iterator}_search`]);
            qs.initFieldset(path, $scope.djangoModel, relations).then((models) => {
                $scope.models = models;
            });
        }

        // Removes state definition defaults and pagination terms
        function stripDefaultParams(params) {
            return _.pick(params, (value, key) => {
                // setting the default value of a term to null in a state definition is a very explicit way to ensure it will NEVER generate a search tag, even with a non-default value
                return defaults[key] !== value && key !== 'page' && key !== 'page_size' && defaults[key] !== null;
            });
        }

        // searchable relationships
        function getRelationshipFields(dataset) {
            let flat = _(dataset).map((value) => {
                return _.keys(value.related);
            }).flatten().uniq().value();
            return flat;
        }

        $scope.toggleKeyPane = function() {
            $scope.showKeyPane = !$scope.showKeyPane;
        };

        $scope.clearAll = function(){
            let cleared = _.cloneDeep(defaults);
            delete cleared.page;
            queryset = cleared;
            $state.go('.', {[$scope.iterator + '_search']: queryset});
            qs.search(path, queryset).then((res) => {
                $scope.dataset = res.data;
                $scope.collection = res.data.results;
            });
            $scope.searchTags = stripDefaultParams(queryset);
        };

        // remove tag, merge new queryset, $state.go
        $scope.remove = function(key) {
            delete queryset[key];
            $state.go('.', {
                [$scope.iterator + '_search']: queryset });
            qs.search(path, queryset).then((res) => {
                $scope.dataset = res.data;
                $scope.collection = res.data.results;
            });
            $scope.searchTags = stripDefaultParams(queryset);
        };

        // add a search tag, merge new queryset, $state.go()
        $scope.add = function(terms) {
            let params = {};

            _.forEach(terms.split(' '), (term) => {
                // if only a value is provided, search using default keys
                if (term.split(':').length === 1) {
                    params = _.merge(params, setDefaults(term));
                } else {
                    params = _.merge(params, qs.encodeParam(term));
                }
            });

            function setDefaults(term) {
                // "name" and "description" are sane defaults for MOST models, but not ALL!
                // defaults may be configured in ListDefinition.defaultSearchParams
                if ($scope.list.defaultSearchParams) {
                    return $scope.list.defaultSearchParams(term);
                } else {
                   return {
                        or__name__icontains: term,
                        or__description__icontains: term
                    };
                }
            }

            params.page = '1';
            queryset = _.merge(queryset, params);
            // https://ui-router.github.io/docs/latest/interfaces/params.paramdeclaration.html#dynamic
            // This transition will not reload controllers/resolves/views
            // but will register new $stateParams[$scope.iterator + '_search'] terms
            $state.go('.', {
                [$scope.iterator + '_search']: queryset });
            qs.search(path, queryset).then((res) => {
                $scope.dataset = res.data;
                $scope.collection = res.data.results;
            });

            $scope.searchTerm = null;
            $scope.searchTags = stripDefaultParams(queryset);
        };

        $scope.decodeParam = function(key, value) {
            return qs.decodeParam(key, value);
        };
    }
];
