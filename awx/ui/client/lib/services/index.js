import EventService from './event.service';
import PathService from './path.service';

angular
    .module('at.lib.services', [])
    .factory('EventService', EventService)
    .factory('PathService', PathService); 
