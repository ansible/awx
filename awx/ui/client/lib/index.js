import EventService from './event.service';
import PathService from './path.service';

angular
    .module('at.lib', [])
    .factory('EventService', EventService)
    .factory('PathService', PathService); 
