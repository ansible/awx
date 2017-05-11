export default 
    [   'templateUrl',
        'Rest',
        '$q',
        '$filter',
        function(templateUrl, Rest, $q, $filter) {
            return {
                restrict: 'E',
                scope: false,
                templateUrl: templateUrl('projects/revisions/revisions'),
                link: function(scope)  {
                    var full_revision = scope.project.scm_revision;
                    console.log(scope.project.scm_revision);
                    scope.seeMoreInactive = true;
                    scope.count = scope.project.scm_revision.length;
                    scope.revisionHash = $filter('limitTo')(full_revision, 7, 0);

                    scope.Copy = function() {
                        console.log('copy');
                    };
                }
            };
        }
    ];