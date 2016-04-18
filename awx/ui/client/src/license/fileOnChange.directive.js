/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
	[function(){
		return {
			restrict: 'A',
			link: function(scope, el, attrs){
				var onChange = scope.$eval(attrs.fileOnChange);
				el.bind('change', onChange);
			}
		};
	}];
