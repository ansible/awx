/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../shared/template-url/template-url.factory';

export default {
	name: 'license',
	route: '/license',
	templateUrl: templateUrl('license/license'),
	controller: 'licenseController',
	data: {},
	ncyBreadcrumb: {
		parent: 'setup',
		label: 'LICENSE'
	}
};
