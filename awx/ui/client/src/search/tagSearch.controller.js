export default ['$scope', 'Refresh', 'tagSearchService',
    function($scope, Refresh, tagSearchService) {
        // JSONify passed field elements that can be searched
        $scope.list = JSON.parse($scope.list);

        // Grab options for the left-dropdown of the searchbar
        tagSearchService.getSearchTypes($scope.list, $scope.endpoint)
            .then(function(searchTypes) {
                $scope.searchTypes = searchTypes;

                // currently selected option of the left-dropdown
                $scope.currentSearchType = $scope.searchTypes[0];
            });

        // shows/hide the search type dropdown
        $scope.toggleTypeDropdown = function() {
            $scope.showTypeDropdown = !$scope.showTypeDropdown;
        };

        // sets the search type dropdown and hides it
        $scope.setSearchType = function(type) {
            $scope.currentSearchType = type;
            $scope.showTypeDropdown = false;
        };

        // if the current search type uses a list instead
        // of a text input, this show hides that list
        $scope.toggleCurrentSearchDropdown = function() {
            $scope
                .showCurrentSearchDropdown = !$scope
                    .showCurrentSearchDropdown;
        };

        $scope.updateSearch = function(tags) {
            var iterator = $scope.iterator;
            var pageSize = $scope
                .$parent[iterator + "_page_size"];
            var set = $scope.set;
            var listScope = $scope.$parent;
            var url = tagSearchService
                .updateFilteredUrl($scope.endpoint, tags, pageSize);

            $scope.$parent[iterator + "_active_search"] = true;

            Refresh({
                scope: listScope,
                set: set,
                iterator: iterator,
                url: url
            });

            $scope.currentSearchFilters = tags;
        };

        // triggers a refilter of the list with the newTag
        $scope.addTag = function(type) {
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

            if (!tagSearchService.isDuplicate(tags, newTag)) {
                tags.push(newTag);
                $scope.updateSearch(tags);
            }
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
        };
    }];
