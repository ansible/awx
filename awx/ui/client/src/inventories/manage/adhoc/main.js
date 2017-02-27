import adhocController from './adhoc.controller';
import form from './adhoc.form';

export default
    angular.module('adhoc', [])
        .controller('adhocController', adhocController)
        .factory('adhocForm', form);
