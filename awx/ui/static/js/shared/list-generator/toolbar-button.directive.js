export default ['$compile', 'Button', function($compile, Button) {
    return {
        restrict: 'E',
        scope: {
            name: '=',
            options: '=',
            onSelected: '&'
        },
        link: function(scope, element, attrs) {
            var html = '';

            // Save the ngClick property from
            // legacy list actions
            scope.action = scope.options.ngClick;


            var btnOptions = _.clone(scope.options);
            btnOptions.ngClick = "onSelected({ action: action })";

            // These should be taken care of by
            // using ng-show & ng-hide on this
            // directive
            delete btnOptions.ngHide;
            delete btnOptions.ngShow;

            // console.log('options:', scope.options);

            html += Button({
                btn: btnOptions,
                action: scope.name,
                toolbar: true
            });

            element.html(html);

            $compile(element.contents())(scope);
        }
    };
}];
