/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import controller from './ansible_facts.controller';

export default
angular.module('AnsibleFacts', [])
    .controller('AnsibleFactsController', controller);
