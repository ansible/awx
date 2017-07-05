import EventService from './event.service';
import PathService from './path.service';
import BaseStringService from './base-string.service';

angular
    .module('at.lib.services', [])
    .service('EventService', EventService)
    .service('PathService', PathService)
    .service('BaseStringService', BaseStringService); 
