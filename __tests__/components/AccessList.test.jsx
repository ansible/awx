import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';

import AccessList from '../../src/components/AccessList';

const mockResults = [
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
          }
        }
      ]
    }
  }
];

const mockUserRoles = [
  {
    id: 2,
    name: 'bar',
  }
];

const mockUserTeams = [
  {
    id: 3,
  }
];

const mockTeamRoles = [
  {
    id: 4,
    name: 'baz',
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
            getUserRoles={() => {}}
            getUserTeams={() => {}}
            getTeamRoles={() => {}}
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
            getAccessList={() => ({ data: { count: 1, results: mockResults } })}
            getUserRoles={() => ({ data: { results: mockUserRoles } })}
            getUserTeams={() => ({ data: { results: mockUserTeams } })}
            getTeamRoles={() => ({ data: { results: mockTeamRoles } })}
          />
        </MemoryRouter>
      </I18nProvider>
    ).find('AccessList');

    setImmediate(() => {
      expect(wrapper.state().results).toEqual(mockResults);
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
            getAccessList={() => ({ data: { count: 1, results: mockResults } })}
            getUserRoles={() => ({ data: { results: mockUserRoles } })}
            getUserTeams={() => ({ data: { results: mockUserTeams } })}
            getTeamRoles={() => ({ data: { results: mockTeamRoles } })}
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
            getAccessList={() => ({ data: { count: 1, results: mockResults } })}
            getUserRoles={() => ({ data: { results: mockUserRoles } })}
            getUserTeams={() => ({ data: { results: mockUserTeams } })}
            getTeamRoles={() => ({ data: { results: mockTeamRoles } })}
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
});
