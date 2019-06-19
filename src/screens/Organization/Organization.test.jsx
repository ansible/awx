import React from 'react';
import { mountWithContexts, waitForElement } from '../../../testUtils/enzymeHelpers';
import Organization from './Organization';
import { OrganizationsAPI } from '../../api';

jest.mock('../../api');

const mockMe = {
  is_super_user: true,
  is_system_auditor: false
};

const mockNoResults = {
  count: 0,
  next: null,
  previous: null,
  data: { results: [] }
};

const mockDetails = {
  data: {
    id: 1,
    type: 'organization',
    url: '/api/v2/organizations/1/',
    related: {
      notification_templates: '/api/v2/organizations/1/notification_templates/',
      notification_templates_any: '/api/v2/organizations/1/notification_templates_any/',
      notification_templates_success: '/api/v2/organizations/1/notification_templates_success/',
      notification_templates_error: '/api/v2/organizations/1/notification_templates_error/',
      object_roles: '/api/v2/organizations/1/object_roles/',
      access_list: '/api/v2/organizations/1/access_list/',
      instance_groups: '/api/v2/organizations/1/instance_groups/'
    },
    summary_fields: {
      created_by: {
        id: 1,
        username: 'admin',
        first_name: 'Super',
        last_name: 'User'
      },
      modified_by: {
        id: 1,
        username: 'admin',
        first_name: 'Super',
        last_name: 'User'
      },
      object_roles: {
        admin_role: {
          description: 'Can manage all aspects of the organization',
          name: 'Admin',
          id: 42
        },
        notification_admin_role: {
          description: 'Can manage all notifications of the organization',
          name: 'Notification Admin',
          id: 1683
        },
        auditor_role: {
          description: 'Can view all aspects of the organization',
          name: 'Auditor',
          id: 41
        },
      },
      user_capabilities: {
        edit: true,
        delete: true
      },
      related_field_counts: {
        users: 51,
        admins: 19,
        inventories: 23,
        teams: 12,
        projects: 33,
        job_templates: 30
      }
    },
    created: '2015-07-07T17:21:26.429745Z',
    modified: '2017-09-05T19:23:15.418808Z',
    name: 'Sarif Industries',
    description: '',
    max_hosts: 0,
    custom_virtualenv: null
  }
};

const adminOrganization = {
  id: 1,
  type: 'organization',
  url: '/api/v2/organizations/1/',
  related: {
    instance_groups: '/api/v2/organizations/1/instance_groups/',
    object_roles: '/api/v2/organizations/1/object_roles/',
    access_list: '/api/v2/organizations/1/access_list/',
  },
  summary_fields: {
    created_by: {
      id: 1,
      username: 'admin',
      first_name: 'Super',
      last_name: 'User'
    },
    modified_by: {
      id: 1,
      username: 'admin',
      first_name: 'Super',
      last_name: 'User'
    },
  },
  created: '2015-07-07T17:21:26.429745Z',
  modified: '2017-09-05T19:23:15.418808Z',
  name: 'Sarif Industries',
  description: '',
  max_hosts: 0,
  custom_virtualenv: null
};

const auditorOrganization = {
  id: 2,
  type: 'organization',
  url: '/api/v2/organizations/2/',
  related: {
    instance_groups: '/api/v2/organizations/2/instance_groups/',
    object_roles: '/api/v2/organizations/2/object_roles/',
    access_list: '/api/v2/organizations/2/access_list/',
  },
  summary_fields: {
    created_by: {
      id: 2,
      username: 'admin',
      first_name: 'Super',
      last_name: 'User'
    },
    modified_by: {
      id: 2,
      username: 'admin',
      first_name: 'Super',
      last_name: 'User'
    },
  },
  created: '2015-07-07T17:21:26.429745Z',
  modified: '2017-09-05T19:23:15.418808Z',
  name: 'Autobots',
  description: '',
  max_hosts: 0,
  custom_virtualenv: null
};

const notificationAdminOrganization = {
  id: 3,
  type: 'organization',
  url: '/api/v2/organizations/3/',
  related: {
    instance_groups: '/api/v2/organizations/3/instance_groups/',
    object_roles: '/api/v2/organizations/3/object_roles/',
    access_list: '/api/v2/organizations/3/access_list/',
  },
  summary_fields: {
    created_by: {
      id: 1,
      username: 'admin',
      first_name: 'Super',
      last_name: 'User'
    },
    modified_by: {
      id: 1,
      username: 'admin',
      first_name: 'Super',
      last_name: 'User'
    },
  },
  created: '2015-07-07T17:21:26.429745Z',
  modified: '2017-09-05T19:23:15.418808Z',
  name: 'Decepticons',
  description: '',
  max_hosts: 0,
  custom_virtualenv: null
};

const allOrganizations = [
  adminOrganization,
  auditorOrganization,
  notificationAdminOrganization
];

async function getOrganizations (params) {
  let results = allOrganizations;
  if (params && params.role_level) {
    if (params.role_level === 'admin_role') {
      results = [adminOrganization];
    }
    if (params.role_level === 'auditor_role') {
      results = [auditorOrganization];
    }
    if (params.role_level === 'notification_admin_role') {
      results = [notificationAdminOrganization];
    }
  }
  return {
    count: results.length,
    next: null,
    previous: null,
    data: { results }
  };
}

describe.only('<Organization />', () => {
  test('initially renders succesfully', () => {
    OrganizationsAPI.readDetail.mockResolvedValue(mockDetails);
    OrganizationsAPI.read.mockImplementation(getOrganizations);
    mountWithContexts(<Organization setBreadcrumb={() => {}} me={mockMe} />);
  });

  test('notifications tab shown for admins', async (done) => {
    OrganizationsAPI.readDetail.mockResolvedValue(mockDetails);
    OrganizationsAPI.read.mockImplementation(getOrganizations);

    const wrapper = mountWithContexts(<Organization setBreadcrumb={() => {}} me={mockMe} />);
    const tabs = await waitForElement(wrapper, '.pf-c-tabs__item', el => el.length === 4);
    expect(tabs.last().text()).toEqual('Notifications');
    done();
  });

  test('notifications tab hidden with reduced permissions', async (done) => {
    OrganizationsAPI.readDetail.mockResolvedValue(mockDetails);
    OrganizationsAPI.read.mockResolvedValue(mockNoResults);

    const wrapper = mountWithContexts(<Organization setBreadcrumb={() => {}} me={mockMe} />);
    const tabs = await waitForElement(wrapper, '.pf-c-tabs__item', el => el.length === 3);
    tabs.forEach(tab => expect(tab.text()).not.toEqual('Notifications'));
    done();
  });
});
