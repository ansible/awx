/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
import LookUpInit from './lookup.factory';
import listGenerator from '../shared/list-generator/main';

export default
    angular.module('LookUpHelper', ['RestServices', 'Utilities', 'SearchHelper',
    'PaginationHelpers', listGenerator.name, 'ApiLoader', 'ModalDialog'])
        .factory('LookUpInit', LookUpInit);
