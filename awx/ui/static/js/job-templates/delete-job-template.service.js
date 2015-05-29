/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 var rest, getBasePath;

export default
    [   'Rest',
        'GetBasePath',
        function(_rest, _getBasePath) {
            rest = _rest;
            getBasePath = _getBasePath;
            return deleteJobTemplate;
        }
    ];

function deleteJobTemplate(id) {
  var url = getBasePath('job_templates');

    url = url + id;

    rest.setUrl(url);
    return rest.destroy();
}
