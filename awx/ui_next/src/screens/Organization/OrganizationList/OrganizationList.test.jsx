import React from 'react';
import { OrganizationsAPI } from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';

import OrganizationsList, { _OrganizationsList } from './OrganizationList';

jest.mock('@api');

const mockAPIOrgsList = {
  data: {
    count: 3,
    results: [
      {
        name: 'Organization 0',
        id: 1,
        url: '/organizations/1',
        summary_fields: {
          related_field_counts: {
            teams: 3,
            users: 4,
          },
          user_capabilities: {
            delete: true,
          },
        },
      },
      {
        name: 'Organization 1',
        id: 2,
        url: '/organizations/2',
        summary_fields: {
          related_field_counts: {
            teams: 2,
            users: 5,
          },
          user_capabilities: {
            delete: true,
          },
        },
      },
      {
        name: 'Organization 2',
        id: 3,
        url: '/organizations/3',
        summary_fields: {
          related_field_counts: {
            teams: 5,
            users: 6,
          },
          user_capabilities: {
            delete: true,
          },
        },
      },
    ],
  },
  isModalOpen: false,
  warningTitle: 'title',
  warningMsg: 'message',
};

describe('<OrganizationsList />', () => {
  let wrapper;

  beforeEach(() => {
    OrganizationsAPI.read = () =>
      Promise.resolve({
        data: {
          count: 0,
          results: [],
        },
      });
    OrganizationsAPI.readOptions = () =>
      Promise.resolve({
        data: {
          actions: {
            GET: {},
            POST: {},
          },
        },
      });
  });

  test('initially renders succesfully', () => {
    mountWithContexts(<OrganizationsList />);
  });

  test('Puts 1 selected Org in state when handleSelect is called.', () => {
    wrapper = mountWithContexts(<OrganizationsList />).find(
      'OrganizationsList'
    );

    wrapper.setState({
      organizations: mockAPIOrgsList.data.results,
      itemCount: 3,
      isInitialized: true,
    });
    wrapper.update();
    expect(wrapper.state('selected').length).toBe(0);
    wrapper.instance().handleSelect(mockAPIOrgsList.data.results.slice(0, 1));
    expect(wrapper.state('selected').length).toBe(1);
  });

  test('Puts all Orgs in state when handleSelectAll is called.', () => {
    wrapper = mountWithContexts(<OrganizationsList />);
    const list = wrapper.find('OrganizationsList');
    list.setState({
      organizations: mockAPIOrgsList.data.results,
      itemCount: 3,
      isInitialized: true,
    });
    expect(list.state('selected').length).toBe(0);
    list.instance().handleSelectAll(true);
    wrapper.update();
    expect(list.state('selected').length).toEqual(
      list.state('organizations').length
    );
  });

  test('api is called to delete Orgs for each org in selected.', () => {
    wrapper = mountWithContexts(<OrganizationsList />);
    const component = wrapper.find('OrganizationsList');
    wrapper.find('OrganizationsList').setState({
      organizations: mockAPIOrgsList.data.results,
      itemCount: 3,
      isInitialized: true,
      isModalOpen: mockAPIOrgsList.isModalOpen,
      selected: mockAPIOrgsList.data.results,
    });
    wrapper.find('ToolbarDeleteButton').prop('onDelete')();
    expect(OrganizationsAPI.destroy).toHaveBeenCalledTimes(
      component.state('selected').length
    );
  });

  test('call loadOrganizations after org(s) have been deleted', () => {
    const fetchOrgs = jest.spyOn(
      _OrganizationsList.prototype,
      'loadOrganizations'
    );
    const event = { preventDefault: () => {} };
    wrapper = mountWithContexts(<OrganizationsList />);
    wrapper.find('OrganizationsList').setState({
      organizations: mockAPIOrgsList.data.results,
      itemCount: 3,
      isInitialized: true,
      selected: mockAPIOrgsList.data.results.slice(0, 1),
    });
    const component = wrapper.find('OrganizationsList');
    component.instance().handleOrgDelete(event);
    expect(fetchOrgs).toBeCalled();
  });

  test('error is shown when org not successfully deleted from api', async done => {
    OrganizationsAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/organizations/1',
          },
          data: 'An error occurred',
        },
      })
    );

    wrapper = mountWithContexts(<OrganizationsList />);
    wrapper.find('OrganizationsList').setState({
      organizations: mockAPIOrgsList.data.results,
      itemCount: 3,
      isInitialized: true,
      selected: mockAPIOrgsList.data.results.slice(0, 1),
    });
    wrapper.find('ToolbarDeleteButton').prop('onDelete')();
    await waitForElement(
      wrapper,
      'Modal',
      el => el.props().isOpen === true && el.props().title === 'Error!'
    );
    done();
  });

  test('Add button shown for users without ability to POST', async done => {
    wrapper = mountWithContexts(<OrganizationsList />);
    await waitForElement(
      wrapper,
      'OrganizationsList',
      el => el.state('hasContentLoading') === true
    );
    await waitForElement(
      wrapper,
      'OrganizationsList',
      el => el.state('hasContentLoading') === false
    );
    expect(wrapper.find('ToolbarAddButton').length).toBe(1);
    done();
  });

  test('Add button hidden for users without ability to POST', async done => {
    OrganizationsAPI.readOptions = () =>
      Promise.resolve({
        data: {
          actions: {
            GET: {},
          },
        },
      });
    wrapper = mountWithContexts(<OrganizationsList />);
    await waitForElement(
      wrapper,
      'OrganizationsList',
      el => el.state('hasContentLoading') === true
    );
    await waitForElement(
      wrapper,
      'OrganizationsList',
      el => el.state('hasContentLoading') === false
    );
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
    done();
  });
});
