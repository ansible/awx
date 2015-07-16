import newMoment from './moment';

export default
    angular.module('moment', ['angularMoment'])
        .config(function() {
            // Remove the global variable for moment
            delete window.moment;
        })
        .constant('moment', newMoment);
