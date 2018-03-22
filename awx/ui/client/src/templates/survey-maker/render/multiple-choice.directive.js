/* jshint unused: vars */
import {templateUrl} from '../../../shared/template-url/template-url.factory';

function link($timeout, CreateSelect2, scope, element, attrs, ngModel) {
    $timeout(function() {

        // select2-ify the dropdown.  If the preview flag is passed here
        // and it's true then we don't want to use a custom dropdown adapter.
        // The reason for this is that the custom dropdown adapter breaks
        // the draggability of this element.  We're able to get away with this
        // in preview mode (survey create/edit) because the element is disabled
        // and we don't actually need the dropdown portion.  Note that the custom
        // dropdown adapter is used to get the dropdown contents to show up in
        // a modal.

        CreateSelect2({
             element: element.find('select'),
             multiple: scope.isMultipleSelect(),
             minimumResultsForSearch: scope.isMultipleSelect() ? Infinity : 10,
             customDropdownAdapter: scope.preview ? false : true
        });
    });

}

export default
    [   '$timeout', 'CreateSelect2',
        function($timeout, CreateSelect2) {
            var directive =
                {   restrict: 'E',
                    require: 'ngModel',
                    scope: {
                        isMultipleSelect: '&multiSelect',
                        choices: '=',
                        question: '=',
                        isRequired: '=ngRequired',
                        selectedValue: '=ngModel',
                        isDisabled: '=ngDisabled',
                        preview: '=',
                        formElementName: '@'
                    },
                    templateUrl: templateUrl('templates/survey-maker/render/multiple-choice'),
                    link: _.partial(link, $timeout, CreateSelect2)
                };
            return directive;
        }
    ];
