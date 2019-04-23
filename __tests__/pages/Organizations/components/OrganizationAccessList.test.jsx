import React from 'react';

import { mountWithContexts } from '../../../enzymeHelpers';
import OrganizationAccessList, { _OrganizationAccessList } from '../../../../src/pages/Organizations/components/OrganizationAccessList';

const mockData = [
  {
    id: 1,
    username: 'boo',
    url: '/foo/bar/',
    first_name: 'john',
    last_name: 'smith',
    summary_fields: {
      foo: [
        {
          role: {
            name: 'foo',
            id: 2,
            user_capabilities: {
              unattach: true
            }
          }
        }
      ]
    }
  }
];

const organization = {
  id: 1,
  name: 'Default',
  summary_fields: {
    object_roles: {},
    user_capabilities: {
      edit: true
    }
  }
};

const api = {
  foo: () => {}
};

describe('<OrganizationAccessList />', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('initially renders succesfully', () => {
    mountWithContexts(
      <OrganizationAccessList
        getAccessList={() => {}}
        removeRole={() => {}}
        api={api}
        organization={organization}
      />
    );
  });

  test('api response data passed to component gets set to state properly', (done) => {
    const wrapper = mountWithContexts(
      <OrganizationAccessList
        getAccessList={() => ({ data: { count: 1, results: mockData } })}
        removeRole={() => {}}
        api={api}
        organization={organization}
      />
    ).find('OrganizationAccessList');

    // expect(wrapper.debug()).toBe(false);

    setImmediate(() => {
      expect(wrapper.state().results).toEqual(mockData);
      done();
    });
  });

  test('onSort being passed properly to DataListToolbar component', async (done) => {
    const onSort = jest.spyOn(_OrganizationAccessList.prototype, 'onSort');
    const wrapper = mountWithContexts(
      <OrganizationAccessList
        getAccessList={() => ({ data: { count: 1, results: mockData } })}
        removeRole={() => {}}
        api={api}
        organization={organization}
      />
    ).find('OrganizationAccessList');
    expect(onSort).not.toHaveBeenCalled();

    setImmediate(() => {
      const rendered = wrapper.update();
      rendered.find('button[aria-label="Sort"]').simulate('click');
      expect(onSort).toHaveBeenCalled();
      done();
    });
  });

  test('getTeamRoles returns empty array if dataset is missing team_id attribute', (done) => {
    const wrapper = mountWithContexts(
      <OrganizationAccessList
        getAccessList={() => ({ data: { count: 1, results: mockData } })}
        removeRole={() => {}}
        api={api}
        organization={organization}
      />
    ).find('OrganizationAccessList');

    setImmediate(() => {
      const { results } = wrapper.state();
      results.forEach(result => {
        expect(result.teamRoles).toEqual([]);
      });
      done();
    });
  });

  test('test handleWarning, confirmDelete, and removeRole methods for Alert component', (done) => {
    const handleWarning = jest.spyOn(_OrganizationAccessList.prototype, 'handleWarning');
    const confirmDelete = jest.spyOn(_OrganizationAccessList.prototype, 'confirmDelete');
    const removeRole = jest.spyOn(_OrganizationAccessList.prototype, 'removeAccessRole');
    const wrapper = mountWithContexts(
      <OrganizationAccessList
        getAccessList={() => ({ data: { count: 1, results: mockData } })}
        removeRole={() => {}}
        api={api}
        organization={organization}
      />
    ).find('OrganizationAccessList');
    expect(handleWarning).not.toHaveBeenCalled();
    expect(confirmDelete).not.toHaveBeenCalled();
    expect(removeRole).not.toHaveBeenCalled();

    setImmediate(() => {
      const rendered = wrapper.update().find('ChipButton');
      rendered.find('button[aria-label="close"]').simulate('click');
      expect(handleWarning).toHaveBeenCalled();
      const alertModal = wrapper.update().find('Modal');
      alertModal.find('button[aria-label="Confirm delete"]').simulate('click');
      expect(confirmDelete).toHaveBeenCalled();
      expect(removeRole).toHaveBeenCalled();
      done();
    });
  });

  test('state is set appropriately when a user tries deleting a role', (done) => {
    const wrapper = mountWithContexts(
      <OrganizationAccessList
        getAccessList={() => ({ data: { count: 1, results: mockData } })}
        removeRole={() => {}}
        api={api}
        organization={organization}
      />
    ).find('OrganizationAccessList');

    setImmediate(() => {
      const expected = [
        {
          deleteType: 'users'
        },
        {
          deleteRoleId: mockData[0].summary_fields.foo[0].role.id
        },
        {
          deleteResourceId: mockData[0].id
        }
      ];
      const rendered = wrapper.update().find('ChipButton');
      rendered.find('button[aria-label="close"]').simulate('click');
      const alertModal = wrapper.update().find('Modal');
      alertModal.find('button[aria-label="Confirm delete"]').simulate('click');
      expect(wrapper.state().warningTitle).not.toBe(null);
      expect(wrapper.state().warningMsg).not.toBe(null);
      expected.forEach(criteria => {
        Object.keys(criteria).forEach(key => {
          expect(wrapper.state()[key]).toEqual(criteria[key]);
        });
      });
      done();
    });
  });
});
