export default
     function ShowDetail($filter, Find, ParseTypeChange, ParseVariableString) {
         return function (params, scope) {

             var activity_id = params.activity_id,
                 activity = Find({ list: params.scope.activities, key: 'id', val: activity_id }),
                 element;

             if (activity) {

                 // Grab our element out of the dom
                 element = angular.element(document.getElementById('stream-detail-modal'));

                 // Grab the modal's scope so that we can set a few variables
                 scope = element.scope();

                 scope.changes = activity.changes;
                 scope.user = ((activity.summary_fields.actor) ? activity.summary_fields.actor.username : 'system') +
                      ' on ' + $filter('longDate')(activity.timestamp);
                 scope.operation = activity.description;
                 scope.settingCategory = _.get(activity, 'summary_fields.setting[0].category');
                 scope.settingName = _.get(activity, 'summary_fields.setting[0].name');
                 scope.header = "Event " + activity.id;

                 scope.variables = ParseVariableString(scope.changes);
                 scope.parseType = 'json';
                 ParseTypeChange({ scope: scope,
                    field_id: 'activity-stream-changes',
                    readOnly: true });
                 scope.parseTypeChange('parseType', 'variables');

                 // Open the modal
                 $('#stream-detail-modal').modal({
                     show: true,
                     backdrop: 'static',
                     keyboard: true
                 });

                 if (!scope.$$phase) {
                     scope.$digest();
                 }
             }

         };
     }

 ShowDetail.$inject = ['$filter', 'Find', 'ParseTypeChange', 'ParseVariableString'];
