import EventService from './event.service';
import PathService from './path.service';

angular
    .module('at.lib.services', [])
    .service('EventService', EventService)
    .service('PathService', PathService); 
