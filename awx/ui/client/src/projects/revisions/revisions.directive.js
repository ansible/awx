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
                    let full_revision = scope.project.scm_revision;
                    scope.revisionHash = $filter('limitTo')(full_revision, 7, 0);
                    scope.count = scope.project.scm_revision.length;

                    scope.copyRevisionHash = function() {
                        let textArea = document.createElement("textarea");

                        // Place in top-left corner of screen regardless of scroll position.
                        textArea.style.position = 'fixed';
                        textArea.style.top = 0;
                        textArea.style.left = 0;

                        // Ensure it has a small width and height. Setting to 1px / 1em
                        // doesn't work as this gives a negative w/h on some browsers.
                        textArea.style.width = '2em';
                        textArea.style.height = '2em';

                        // We don't need padding, reducing the size if it does flash render.
                        textArea.style.padding = 0;

                        // Clean up any borders.
                        textArea.style.border = 'none';
                        textArea.style.outline = 'none';
                        textArea.style.boxShadow = 'none';

                        // Avoid flash of white box if rendered for any reason.
                        textArea.style.background = 'transparent';

                        textArea.value = full_revision;
                        document.body.appendChild(textArea);
                        textArea.select();
                        
                        document.execCommand('copy');

                        document.body.removeChild(textArea);
                    };
                }
            };
        }
    ];