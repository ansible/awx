export default
    [   'templateUrl',
        '$rootScope',
        function(templateUrl, $rootScope) {
            return {
                restrict: 'E',
                templateUrl: templateUrl('shared/icon/icon'),
                scope: {
                },
                link: function(scope, element, attrs) {

                    function buildSvgs() {
                        var svg = $('svg', element);
                        var iconPath = '#' + attrs.name;

                        if ($(iconPath).length === 0) {
                          return;
                        }

                        // Make a copy of the <symbol> tag to insert its contents into this
                        // element's svg tag
                        var content = $(iconPath).clone();

                        // Copy classes & viewBox off the <symbol> so that we preserve any styling
                        // when we copy the item inline
                        var classes = $(iconPath).attr('class');

                        // viewBox needs to be access via native
                        // javascript's setAttribute function
                        var viewBox = $(iconPath)[0].getAttribute('viewBox');

                        svg[0].setAttribute('viewBox', viewBox);
                        svg.attr('class', classes)
                            .html(content.contents());
                    }

                    $rootScope.$on('include-svg.svg-ready', function() {
                        buildSvgs();
                    });

                    buildSvgs();

                }
            };
        }
    ];
