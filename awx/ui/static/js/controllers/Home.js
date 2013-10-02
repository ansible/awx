/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *
 *  Home.js
 *  
 *  Controller functions for Home tab
 *
 */

'use strict';

function Home ($routeParams, $scope, $rootScope, $location, Wait, ObjectCount, ClearScope)
{
    ClearScope('home');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                         //scope.

    var waitCount = 1;
    var loadedCount = 0;
    
    if (!$routeParams['login']) {
        // If we're not logging in, start the Wait widget. Otherwise, it's already running.
        Wait('start');
    }

    ObjectCount({ target: 'container1' });
     
    $rootScope.$on('WidgetLoaded', function() {
        // Once all the widget report back 'loaded', turn off Wait widget
        loadedCount++; 
        if ( loadedCount == waitCount ) {
           Wait('stop');
        }
        });
}

Home.$inject=[ '$routeParams', '$scope', '$rootScope', '$location', 'Wait', 'ObjectCount', 'ClearScope'];