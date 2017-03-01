/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import listGenerator from './list-generator/main';
import formGenerator from './form-generator';
import lookupModal from './lookup/main';
import smartSearch from './smart-search/main';
import paginate from './paginate/main';
import columnSort from './column-sort/main';
import lodashAsPromised from './lodash-as-promised';
import stringFilters from './string-filters/main';
import truncatedText from './truncated-text.directive';
import stateExtender from './stateExtender.provider';
import rbacUiControl from './rbacUiControl';
import socket from './socket/main';
import templateUrl from './template-url/main';
import RestServices from '../rest/main';
import stateDefinitions from './stateDefinitions.factory';
import apiLoader from './api-loader';
import variables from './variables/main';
import parse from './parse/main';
import loadconfig from './load-config/main';
import 'angular-duration-format';

export default
angular.module('shared', [listGenerator.name,
        formGenerator.name,
        lookupModal.name,
		smartSearch.name,
        paginate.name,
        columnSort.name,
        stringFilters.name,
        'ui.router',
        rbacUiControl.name,
        socket.name,
        templateUrl.name,
        RestServices.name,
        apiLoader.name,
        variables.name,
        parse.name,
        loadconfig.name,
        require('angular-cookies'),
        'angular-duration-format'
    ])
    .factory('stateDefinitions', stateDefinitions)
    .factory('lodashAsPromised', lodashAsPromised)
    .directive('truncatedText', truncatedText)
    .provider('$stateExtender', stateExtender);
