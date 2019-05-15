import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../enzymeHelpers';
import OrganizationsList, { _OrganizationsList } from '../../../../src/pages/Organizations/screens/OrganizationsList';

const mockAPIOrgsList = {
  data: {
    count: 3,
    results: [{
      name: 'Organization 0',
      id: 1,
      url: '/organizations/1',
      summary_fields: {
        related_field_counts: {
          teams: 3,
          users: 4
        },
        user_capabilities: {
          delete: true
        }
      },
    },
    {
      name: 'Organization 1',
      id: 2,
      url: '/organizations/2',
      summary_fields: {
        related_field_counts: {
          teams: 2,
          users: 5
        },
        user_capabilities: {
          delete: true
        }
      },
    },
    {
      name: 'Organization 2',
      id: 3,
      url: '/organizations/3',
      summary_fields: {
        related_field_counts: {
          teams: 5,
          users: 6
        },
        user_capabilities: {
          delete: true
        }
      },
    }]
  },
  isModalOpen: false,
  warningTitle: 'title',
  warningMsg: 'message'
};

describe('<OrganizationsList />', () => {
  let wrapper;
  let api;

  beforeEach(() => {
    api = {
      getOrganizations: () => {},
      destroyOrganization: jest.fn(),
    };
  });

  test('initially renders succesfully', () => {
    mountWithContexts(
      <OrganizationsList />
    );
  });

  test('Puts 1 selected Org in state when handleSelect is called.', () => {
    wrapper = mountWithContexts(
      <OrganizationsList />
    ).find('OrganizationsList');

    wrapper.setState({
      organizations: mockAPIOrgsList.data.results,
      itemCount: 3,
      isInitialized: true
    });
    wrapper.update();
    expect(wrapper.state('selected').length).toBe(0);
    wrapper.instance().handleSelect(mockAPIOrgsList.data.results.slice(0, 1));
    expect(wrapper.state('selected').length).toBe(1);
  });

  test('Puts all Orgs in state when handleSelectAll is called.', () => {
    wrapper = mountWithContexts(
      <OrganizationsList />
    );
    const list = wrapper.find('OrganizationsList');
    list.setState({
      organizations: mockAPIOrgsList.data.results,
      itemCount: 3,
      isInitialized: true
    });
    expect(list.state('selected').length).toBe(0);
    list.instance().handleSelectAll(true);
    wrapper.update();
    expect(list.state('selected').length)
      .toEqual(list.state('organizations').length);
  });

  test('api is called to delete Orgs for each org in selected.', () => {
    const fetchOrganizations = jest.fn(() => wrapper.find('OrganizationsList').setState({
      organizations: []
    }));
    wrapper = mountWithContexts(
      <OrganizationsList
        fetchOrganizations={fetchOrganizations}
      />, {
        context: { network: { api } }
      }
    );
    const component = wrapper.find('OrganizationsList');
    wrapper.find('OrganizationsList').setState({
      organizations: mockAPIOrgsList.data.results,
      itemCount: 3,
      isInitialized: true,
      isModalOpen: mockAPIOrgsList.isModalOpen,
      selected: mockAPIOrgsList.data.results
    });
    wrapper.find('ToolbarDeleteButton').prop('onDelete')();
    expect(api.destroyOrganization).toHaveBeenCalledTimes(component.state('selected').length);
  });

  test('call fetchOrganizations after org(s) have been deleted', () => {
    const fetchOrgs = jest.spyOn(_OrganizationsList.prototype, 'fetchOrganizations');
    const event = { preventDefault: () => { } };
    wrapper = mountWithContexts(
      <OrganizationsList />, {
        context: { network: { api } }
      }
    );
    wrapper.find('OrganizationsList').setState({
      organizations: mockAPIOrgsList.data.results,
      itemCount: 3,
      isInitialized: true,
      selected: mockAPIOrgsList.data.results.slice(0, 1)
    });
    const component = wrapper.find('OrganizationsList');
    component.instance().handleOrgDelete(event);
    expect(fetchOrgs).toBeCalled();
  });

  test('error is thrown when org not successfully deleted from api', async () => {
    const history = createMemoryHistory({
      initialEntries: ['organizations?order_by=name&page=1&page_size=5'],
    });
    const handleError = jest.fn();
    wrapper = mountWithContexts(
      <OrganizationsList />, {
        context: {
          router: { history }, network: { api, handleHttpError: handleError }
        }
      }
    );
    await wrapper.setState({
      organizations: mockAPIOrgsList.data.results,
      itemCount: 3,
      isInitialized: true,
      selected: [...mockAPIOrgsList.data.results].push({
        name: 'Organization 6',
        id: 'a',
      })
    });
    wrapper.update();
    const component = wrapper.find('OrganizationsList');
    component.instance().handleOrgDelete();
    expect(handleError).toHaveBeenCalled();
  });
});
