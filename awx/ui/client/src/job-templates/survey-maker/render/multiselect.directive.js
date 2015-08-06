/* jshint unused: vars */

/**
 * @ngdoc
 *
 * @name jobTemplates.surveyMaker.render.multiSelect
 * @description
 *  Angular provides no method of binding to "multiple" for
 *  select lists. This is because under normal circumstances,
 *  the structure of `ng-model` changes based on whether `multiple`
 *  is true or false. We're not needing to "bind" to "multiple",
 *  but we do need to pass in the value dynamically. This allows
 *  us to do that.
 */

var directive =
    {   require: 'ngModel',
        compile: function() {
            return {
                pre: function(scope, element, attrs, ngModel) {
                    if (_.isUndefined(scope.isMultipleSelect)) {
                        return;
                    }

                    if (!scope.isMultipleSelect()) {
                        return;
                    }

                    element.attr('multiple', true);
                    attrs.multiple = true;


                }
            };
        },
        priority: 1000
    };

export default
    function() {
        return directive;
    }
