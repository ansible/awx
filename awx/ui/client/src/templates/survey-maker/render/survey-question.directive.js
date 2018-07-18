/* jshint unused: vars */
import {templateUrl} from '../../../shared/template-url/template-url.factory';

/**
 * @ngdoc directive
 * @name jobTemplates.surveyMaker.render.surveyQuestion
 * @description
 *  Directive that will eventually hold all logic
 *  for rendering different form controls based on
 *  the question type for a survey.
 */

// Since we're generating HTML for the entire survey, and _then_
// calling $compile, this directive never actually gets compiled
// with the question object we need. Therefore, we give it the index
// of the question as an attribute (not scope) and then look it up
// in the `survey_questions` by that index when it the directive gets
// compiled.
//
function findQuestionByIndex(questions, index) {
    return _.find(questions, function(question) {
        return question.index === index;
    });
}

function link($sce, $filter, Empty, scope, element, attrs) {

    function serialize(expression) {
        return $sce.getTrustedHtml(expression);
    }

    function sanitizeDefault() {

        var defaultValue = "",
        min,
        max;

        if(scope.question.type === 'text'|| scope.question.type === "password" ){
            defaultValue = (scope.question.default) ? scope.question.default : "";
            defaultValue = $filter('sanitize')(defaultValue);
            defaultValue = serialize(defaultValue);
        }

        if(scope.question.type === "textarea"){
            defaultValue = (scope.question.default) ? scope.question.default : (scope.question.default_textarea) ? scope.question.default_textarea:  "" ;
            defaultValue =  $filter('sanitize')(defaultValue);
            defaultValue = serialize(defaultValue);
        }

        if(scope.question.type === 'multiplechoice' || scope.question.type === "multiselect"){

            scope.question.default = scope.question.default_multiselect || scope.question.default;

            if (scope.question.default) {
                if (scope.question.type === 'multiselect' && typeof scope.question.default.split === 'function') {
                    defaultValue = scope.question.default.split('\n');
                } else if (scope.question.type !== 'multiselect') {
                    defaultValue = scope.question.default;
                }
            } else {
                defaultValue = '';
            }
        }

        if(scope.question.type === 'integer'){
            min = (!Empty(scope.question.min)) ? scope.question.min : "";
            max = (!Empty(scope.question.max)) ? scope.question.max : "" ;
            defaultValue = (!Empty(scope.question.default)) ? scope.question.default : (!Empty(scope.question.default_int)) ? scope.question.default_int : "" ;

        }
        if(scope.question.type === "float"){
            min = (!Empty(scope.question.min)) ? scope.question.min : "";
            max = (!Empty(scope.question.max)) ? scope.question.max : "" ;
            defaultValue = (!Empty(scope.question.default)) ? scope.question.default : (!Empty(scope.question.default_float)) ? scope.question.default_float : "" ;

        }

        scope.defaultValue = defaultValue;

    }

    //for toggling the input on password inputs
    scope.toggleInput = function(id) {
        var buttonId = id + "_show_input_button",
            inputId = id,
            buttonInnerHTML = $(buttonId).html();
        if (buttonInnerHTML.indexOf("SHOW") > -1) {
            $(buttonId).html("HIDE");
            $(inputId).attr("type", "text");
        } else {
            $(buttonId).html("SHOW");
            $(inputId).attr("type", "password");
        }
    };

    if (!scope.question) {
        scope.question = findQuestionByIndex(scope.surveyQuestions, Number(attrs.index));
    }

    // Split out choices to be consumed by the multiple-choice directive
    if (!_.isUndefined(scope.question.choices)) {
        scope.choices = typeof scope.question.choices.split === 'function' ? scope.question.choices.split('\n') : scope.question.choices;
    }

    sanitizeDefault();

}

export default
    [
        '$sce', '$filter', 'Empty',
        function($sce, $filter, Empty) {
            var directive =
                {   restrict: 'E',
                    scope:
                        {   question: '=',
                            surveyQuestions: '=',
                            isRequired: '@ngRequired',
                            isDisabled: '@ngDisabled',
                            preview: '='
                        },
                    templateUrl: templateUrl('templates/survey-maker/render/survey-question'),
                    link: _.partial(link, $sce, $filter, Empty)
                };

            return directive;
        }
    ];
