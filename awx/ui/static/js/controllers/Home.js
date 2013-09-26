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
    //ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.
    if (!$routeParams['login']) {
       Wait('start');
    }
    
    ObjectCount({ target: 'container1' });

    if (!$routeParams['login']) {
       Wait('stop');
    }
    
}

Home.$inject=[ '$routeParams', '$scope', '$rootScope', '$location', 'Wait', 'ObjectCount', 'ClearScope'];