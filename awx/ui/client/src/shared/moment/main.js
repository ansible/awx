import newMoment from './moment';

export default
    angular.module('moment', [require('angular-moment').name])
        .config(function() {
            // Remove the global variable for moment
            delete window.moment;
        })
        .constant('moment', newMoment);
