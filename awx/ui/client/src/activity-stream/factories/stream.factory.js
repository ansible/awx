export default
     function Stream($rootScope, $state, BuildDescription, ShowDetail) {
         return function (params) {

         var scope = params.scope;

         $rootScope.flashMessage = null;

         // descriptive title describing what AS is showing
         scope.streamTitle = (params && params.title) ? params.title : null;

         scope.refreshStream = function () {
             $state.go('.', null, {reload: true});
         };

         scope.showDetail = function (id) {
             ShowDetail({
                 scope: scope,
                 activity_id: id
             });
         };

         if(scope.activities && scope.activities.length > 0) {
             buildUserAndDescription();
         }

         scope.$watch('activities', function(){
             // Watch for future update to scope.activities (like page change, column sort, search, etc)
             buildUserAndDescription();
         });

         function buildUserAndDescription(){
             scope.activities.forEach(function(activity, i) {
                 // build activity.user
                 if (scope.activities[i].summary_fields.actor) {
                     scope.activities[i].user = "<a href=\"/#/users/" + scope.activities[i].summary_fields.actor.id  + "\">" +
                         scope.activities[i].summary_fields.actor.username + "</a>";
                 } else {
                     scope.activities[i].user = 'system';
                 }
                 // build description column / action text
                 BuildDescription(scope.activities[i]);

             });
         }

     };
 }

 Stream.$inject = ['$rootScope', '$state', 'BuildDescription', 'ShowDetail'];
