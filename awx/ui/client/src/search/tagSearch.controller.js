export default ['$scope', 'Refresh', 'tagSearchService', '$stateParams',
    function($scope, Refresh, tagSearchService, $stateParams) {
        // JSONify passed field elements that can be searched
        $scope.list = angular.fromJson($scope.list);
        // Access config lines from list spec
        $scope.listConfig = $scope.$parent.list;
        // Grab options for the left-dropdown of the searchbar
        if($stateParams.id !== "null"){
            tagSearchService.getSearchTypes($scope.list, $scope.endpoint)
                .then(function(searchTypes) {
                    $scope.searchTypes = searchTypes;

                    // currently selected option of the left-dropdown
                    $scope.currentSearchType = $scope.searchTypes[0];
                });
        }

        // shows/hide the search type dropdown
        $scope.toggleTypeDropdown = function() {
            if ($scope.searchTypes.length > 1) {
                $scope.showTypeDropdown = !$scope.showTypeDropdown;
                if ($scope.showTypeDropdown) {
                    $("body").append("<div class='TagSearch-clickToClose'></div>");
                    $(".TagSearch-clickToClose").on("click", function() {
                        $scope.$apply(function() {
                            $scope.showTypeDropdown = false;
                        });
                        $(".TagSearch-clickToClose").remove();
                    });
                }
            }
        };

        // sets the search type dropdown and hides it
        $scope.setSearchType = function($event, type) {
            $scope.currentSearchType = type;
            $scope.showTypeDropdown = false;
            $(".TagSearch-clickToClose").remove();
            $event.stopPropagation();
        };

        // if the current search type uses a list instead
        // of a text input, this show hides that list
        $scope.toggleCurrentSearchDropdown = function() {
            $scope
                .showCurrentSearchDropdown = !$scope
                    .showCurrentSearchDropdown;
            if ($scope.showCurrentSearchDropdown) {
                $("body").append("<div class='TagSearch-clickToClose'></div>");
                $(".TagSearch-clickToClose").on("click", function() {
                    $scope.$apply(function() {
                        $scope.showCurrentSearchDropdown = false;
                    });
                    $(".TagSearch-clickToClose").remove();
                });
            }
};

        $scope.updateSearch = function(tags) {
            var iterator = $scope.iterator;
            var pageSize = $scope
                .$parent[iterator + "_page_size"];
            var searchParams = $scope
                .$parent[iterator + "SearchParams"];
            var set = $scope.set;
            var listScope = $scope.$parent;
            var url = tagSearchService
                .updateFilteredUrl($scope.endpoint, tags, pageSize, searchParams);

            $scope.$parent[iterator + "_active_search"] = true;
            Refresh({
                scope: listScope,
                set: set,
                iterator: iterator,
                url: url
            });

            listScope.$on('PostRefresh', function() {
                if (set === 'notifications') {
                    $scope.$emit('relatednotifications');
                }
            });

            $scope.currentSearchFilters = tags;
        };

        // triggers a refilter of the list with the newTag
        $scope.addTag = function($event, type) {
            var newTag = tagSearchService
                .getTag($scope.currentSearchType,
                    $scope.newSearchTag,
                    type);

            // reset the search bar
            $scope.resetSearchBar();

            // make a clone of the currentSearchFilters
            // array and push the newTag to this array
            var tags = tagSearchService
                .getCurrentTags($scope
                    .currentSearchFilters);

            if (!tagSearchService.isDuplicate(tags, newTag) && !!newTag.name) {
                tags.push(newTag);
                $scope.updateSearch(tags);
            }
            $event.stopPropagation();
        };

        // triggers a refilter of the list without the oldTag
        $scope.deleteTag = function(oldTag) {
            // make a clone of the currentSearchFilters
            // array and remove oldTag from the array
            var tags = tagSearchService
                .getCurrentTags($scope
                    .currentSearchFilters)
                .filter(function(tag) {
                    return tag.url !== oldTag.url;
                });

            $scope.updateSearch(tags);
        };

        // make sure all stateful UI triggers are reset
        $scope.resetSearchBar = function() {
            delete $scope.currentSearchSelectedOption;
            $scope.newSearchTag = null;
            $scope.showTypeDropdown = false;
            $scope.showCurrentSearchDropdown = false;
            $(".TagSearch-clickToClose").remove();
        };
    }];
