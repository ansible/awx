import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';

import AccessList from '../../src/components/AccessList';

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
          }
        }
      ],
    }
  }
];

describe('<AccessList />', () => {
  test('initially renders succesfully', () => {
    mount(
      <I18nProvider>
        <MemoryRouter>
          <AccessList
            match={{ path: '/organizations/:id', url: '/organizations/1', params: { id: '1' } }}
            location={{ search: '', pathname: '/organizations/1/access' }}
            getAccessList={() => {}}
            removeRole={() => {}}
          />
        </MemoryRouter>
      </I18nProvider>
    );
  });

  test('api response data passed to component gets set to state properly', (done) => {
    const wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <AccessList
            match={{ path: '/organizations/:id', url: '/organizations/1', params: { id: '0' } }}
            location={{ search: '', pathname: '/organizations/1/access' }}
            getAccessList={() => ({ data: { count: 1, results: mockData } })}
            removeRole={() => {}}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('AccessList');

    setImmediate(() => {
      expect(wrapper.state().results).toEqual(mockData);
      done();
    });
  });

  test('onExpand and onCompact methods called when user clicks on Expand and Compact icons respectively', async (done) => {
    const onExpand = jest.spyOn(AccessList.prototype, 'onExpand');
    const onCompact = jest.spyOn(AccessList.prototype, 'onCompact');
    const wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <AccessList
            match={{ path: '/organizations/:id', url: '/organizations/1', params: { id: '0' } }}
            location={{ search: '', pathname: '/organizations/1/access' }}
            getAccessList={() => ({ data: { count: 1, results: mockData } })}
            removeRole={() => {}}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('AccessList');
    expect(onExpand).not.toHaveBeenCalled();
    expect(onCompact).not.toHaveBeenCalled();

    setImmediate(() => {
      const rendered = wrapper.update();
      rendered.find('button[aria-label="Expand"]').simulate('click');
      rendered.find('button[aria-label="Collapse"]').simulate('click');
      expect(onExpand).toHaveBeenCalled();
      expect(onCompact).toHaveBeenCalled();
      done();
    });
  });

  test('onSort being passed properly to DataListToolbar component', async (done) => {
    const onSort = jest.spyOn(AccessList.prototype, 'onSort');
    const wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <AccessList
            match={{ path: '/organizations/:id', url: '/organizations/1', params: { id: '0' } }}
            location={{ search: '', pathname: '/organizations/1/access' }}
            getAccessList={() => ({ data: { count: 1, results: mockData } })}
            removeRole={() => {}}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('AccessList');
    expect(onSort).not.toHaveBeenCalled();

    setImmediate(() => {
      const rendered = wrapper.update();
      rendered.find('button[aria-label="Sort"]').simulate('click');
      expect(onSort).toHaveBeenCalled();
      done();
    });
  });

  test('getTeamRoles returns empty array if dataset is missing team_id attribute', (done) => {
    const wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <AccessList
            match={{ path: '/organizations/:id', url: '/organizations/1', params: { id: '0' } }}
            location={{ search: '', pathname: '/organizations/1/access' }}
            getAccessList={() => ({ data: { count: 1, results: mockData } })}
            removeRole={() => {}}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('AccessList');

    setImmediate(() => {
      const { results } = wrapper.state();
      results.forEach(result => {
        expect(result.teamRoles).toEqual([]);
      });
      done();
    });
  });

  test('test handleWarning, confirmDelete, and removeRole methods for Alert component', (done) => {
    const handleWarning = jest.spyOn(AccessList.prototype, 'handleWarning');
    const confirmDelete = jest.spyOn(AccessList.prototype, 'confirmDelete');
    const removeRole = jest.spyOn(AccessList.prototype, 'removeAccessRole');
    const wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <AccessList
            match={{ path: '/organizations/:id', url: '/organizations/1', params: { id: '0' } }}
            location={{ search: '', pathname: '/organizations/1/access' }}
            getAccessList={() => ({ data: { count: 1, results: mockData } })}
            removeRole={() => {}}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('AccessList');
    expect(handleWarning).not.toHaveBeenCalled();
    expect(confirmDelete).not.toHaveBeenCalled();
    expect(removeRole).not.toHaveBeenCalled();

    setImmediate(() => {
      const rendered = wrapper.update().find('ChipButton');
      rendered.find('button[aria-label="close"]').simulate('click');
      expect(handleWarning).toHaveBeenCalled();
      const alert = wrapper.update().find('Alert');
      alert.find('button[aria-label="confirm-delete"]').simulate('click');
      expect(confirmDelete).toHaveBeenCalled();
      expect(removeRole).toHaveBeenCalled();
      done();
    });
  });

  test('state is set appropriately when a user tries deleting a role', (done) => {
    const wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <AccessList
            match={{ path: '/organizations/:id', url: '/organizations/1', params: { id: '0' } }}
            location={{ search: '', pathname: '/organizations/1/access' }}
            getAccessList={() => ({ data: { count: 1, results: mockData } })}
            removeRole={() => {}}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('AccessList');

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
      const alert = wrapper.update().find('Alert');
      alert.find('button[aria-label="confirm-delete"]').simulate('click');
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
