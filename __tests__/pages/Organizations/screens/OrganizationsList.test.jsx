import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../enzymeHelpers';
import OrganizationsList, { _OrganizationsList } from '../../../../src/pages/Organizations/screens/OrganizationsList';

const mockAPIOrgsList = {
  data: {
    results: [{
      name: 'Organization 0',
      id: 1,
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

describe('<_OrganizationsList />', () => {
  let wrapper;
  let api;

  beforeEach(() => {
    api = {
      getOrganizations: jest.fn(),
      destroyOrganization: jest.fn(),
    };
  });

  test('initially renders succesfully', () => {
    mountWithContexts(
      <OrganizationsList />
    );
  });

  test('Puts 1 selected Org in state when onSelect is called.', async () => {
    wrapper = mountWithContexts(
      <OrganizationsList />
    ).find('OrganizationsList');
    await setImmediate(async () => {
      wrapper.setState({
        results: mockAPIOrgsList.data.results
      });
      wrapper.update();
    });
    wrapper.instance().onSelect(mockAPIOrgsList.data.results.slice(0, 1));
    expect(wrapper.state('selected').length).toBe(1);
  });

  test('Puts all Orgs in state when onSelectAll is called.', async () => {
    wrapper = mountWithContexts(
      <OrganizationsList />
    ).find('OrganizationsList');
    wrapper.setState(
      mockAPIOrgsList.data
    );
    wrapper.find({ type: 'checkbox' }).simulate('click');
    wrapper.instance().onSelectAll(true);
    expect(wrapper.find('OrganizationsList').state().selected.length).toEqual(wrapper.state().results.length);
  });

  test('orgsToDelete is 0 when close modal button is clicked.', async () => {
    wrapper = mountWithContexts(
      <OrganizationsList />
    );
    wrapper.find('OrganizationsList').setState({
      results: mockAPIOrgsList.data.results,
      isModalOpen: mockAPIOrgsList.isModalOpen,
      selected: mockAPIOrgsList.data.results
    });
    const component = wrapper.find('OrganizationsList');
    wrapper.find('DataListToolbar').prop('onOpenDeleteModal')();
    wrapper.update();
    const button = wrapper.find('ModalBoxCloseButton');
    button.prop('onClose')();
    wrapper.update();
    expect(component.state('isModalOpen')).toBe(false);
    expect(component.state('selected').length).toBe(0);
    wrapper.unmount();
  });

  test('orgsToDelete is 0 when cancel modal button is clicked.', async () => {
    wrapper = mountWithContexts(
      <OrganizationsList />
    );
    wrapper.find('OrganizationsList').setState({
      results: mockAPIOrgsList.data.results,
      isModalOpen: mockAPIOrgsList.isModalOpen,
      selected: mockAPIOrgsList.data.results
    });
    const component = wrapper.find('OrganizationsList');
    wrapper.find('DataListToolbar').prop('onOpenDeleteModal')();
    wrapper.update();
    const button = wrapper.find('ModalBoxFooter').find('button').at(1);
    button.prop('onClick')();
    wrapper.update();
    expect(component.state('isModalOpen')).toBe(false);
    expect(component.state('selected').length).toBe(0);
    wrapper.unmount();
  });

  test('api is called to delete Orgs for each org in orgsToDelete.', async () => {
    const fetchOrganizations = jest.fn(() => wrapper.find('OrganizationsList').setState({
      results: []
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
      results: mockAPIOrgsList.data.results,
      isModalOpen: mockAPIOrgsList.isModalOpen,
      selected: mockAPIOrgsList.data.results
    });
    wrapper.find('DataListToolbar').prop('onOpenDeleteModal')();
    wrapper.update();
    const button = wrapper.find('ModalBoxFooter').find('button').at(0);
    button.simulate('click');
    wrapper.update();
    expect(api.destroyOrganization).toHaveBeenCalledTimes(component.state('results').length);
  });

  test('call fetchOrganizations after org(s) have been deleted', async () => {
    const fetchOrgs = jest.spyOn(_OrganizationsList.prototype, 'fetchOrganizations');
    const event = { preventDefault: () => { } };
    wrapper = mountWithContexts(
      <OrganizationsList />, {
        context: { network: { api } }
      }
    );
    wrapper.find('OrganizationsList').setState({
      results: mockAPIOrgsList.data.results,
      selected: mockAPIOrgsList.data.results.slice(0, 1)
    });
    const component = wrapper.find('OrganizationsList');
    await component.instance().handleOrgDelete(event);
    expect(fetchOrgs).toBeCalled();
  });

  test('url updates properly', async () => {
    const history = createMemoryHistory({
      initialEntries: ['organizations?order_by=name&page=1&page_size=5'],
    });
    wrapper = mountWithContexts(
      <OrganizationsList />, {
        context: { router: { history } }
      }
    );
    const component = wrapper.find('OrganizationsList');
    component.instance().updateUrl({
      page: 1,
      page_size: 5,
      order_by: 'modified'
    });
    expect(history.location.search).toBe('?order_by=modified&page=1&page_size=5');
  });

  test('onSort sends the correct information to fetchOrganizations', async () => {
    const history = createMemoryHistory({
      initialEntries: ['organizations?order_by=name&page=1&page_size=5'],
    });
    const fetchOrganizations = jest.spyOn(_OrganizationsList.prototype, 'fetchOrganizations');
    wrapper = mountWithContexts(
      <OrganizationsList />, {
        context: {
          router: { history }
        }
      }
    );
    const component = wrapper.find('OrganizationsList');
    component.instance().onSort('modified', 'ascending');
    expect(fetchOrganizations).toBeCalledWith({
      page: 1,
      page_size: 5,
      order_by: 'modified'
    });
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
    await setImmediate(async () => {
      wrapper.setState({
        results: mockAPIOrgsList.data.results,
        selected: [...mockAPIOrgsList.data.results].push({ id: 'a' })
      });
      wrapper.update();
    });
    const component = wrapper.find('OrganizationsList');
    component.instance().handleOrgDelete();
    expect(handleError).toBeCalled();
  });
});
