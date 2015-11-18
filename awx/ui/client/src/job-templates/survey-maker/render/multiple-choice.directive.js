/* jshint unused: vars */
import {templateUrl} from '../../../shared/template-url/template-url.factory';

function link($timeout, scope, element, attrs, ngModel) {
    attrs.width = attrs.width || '100%';

    $timeout(function() {

        $.fn.select2.amd.require(
            [   'select2/utils',
                'select2/dropdown',
                'select2/dropdown/search',
                'select2/dropdown/attachContainer',
                'select2/dropdown/closeOnSelect',
                'select2/dropdown/minimumResultsForSearch'
            ],
            function(Utils, Dropdown, Search, AttachContainer, CloseOnSelect, MinimumResultsForSearch) {

                var CustomAdapter =
                    _.reduce([Search, AttachContainer, CloseOnSelect, MinimumResultsForSearch],
                             function(Adapter, Decorator) {
                                 return Utils.Decorate(Adapter, Decorator);
                             }, Dropdown);

                element.find('select').select2(
                    {   multiple: scope.isMultipleSelect(),
                        minimumResultsForSearch: Infinity,
                        theme: 'bootstrap',
                        width: attrs.width,
                        dropdownAdapter: CustomAdapter
                    });
            });

    });

}

export default
    [   '$timeout',
        function($timeout) {
            var directive =
                {   restrict: 'E',
                    require: 'ngModel',
                    scope: {
                        isMultipleSelect: '&multiSelect',
                        choices: '=',
                        question: '=',
                        isRequired: '=ngRequired',
                        selectedValue: '=ngModel',
                        isDisabled: '=ngDisabled'
                    },
                    templateUrl: templateUrl('job-templates/survey-maker/render/multiple-choice'),
                    link: _.partial(link, $timeout)
                };
            return directive;
        }
    ];
