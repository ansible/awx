import React from 'react';
import { HostsAPI } from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';

import HostsList, { _HostsList } from './HostList';

jest.mock('@api');

const mockHosts = [
  {
    id: 1,
    name: 'Host 1',
    url: '/api/v2/hosts/1',
    inventory: 1,
    summary_fields: {
      inventory: {
        id: 1,
        name: 'inv 1',
      },
      user_capabilities: {
        delete: true,
        update: true,
      },
    },
  },
  {
    id: 2,
    name: 'Host 2',
    url: '/api/v2/hosts/2',
    inventory: 1,
    summary_fields: {
      inventory: {
        id: 1,
        name: 'inv 1',
      },
      user_capabilities: {
        delete: true,
        update: true,
      },
    },
  },
  {
    id: 3,
    name: 'Host 3',
    url: '/api/v2/hosts/3',
    inventory: 1,
    summary_fields: {
      inventory: {
        id: 1,
        name: 'inv 1',
      },
      user_capabilities: {
        delete: false,
        update: false,
      },
    },
  },
];

describe('<HostsList />', () => {
  beforeEach(() => {
    HostsAPI.read.mockResolvedValue({
      data: {
        count: mockHosts.length,
        results: mockHosts,
      },
    });

    HostsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders successfully', () => {
    mountWithContexts(
      <HostsList
        match={{ path: '/hosts', url: '/hosts' }}
        location={{ search: '', pathname: '/hosts' }}
      />
    );
  });

  test('Hosts are retrieved from the api and the components finishes loading', async done => {
    const loadHosts = jest.spyOn(_HostsList.prototype, 'loadHosts');
    const wrapper = mountWithContexts(<HostsList />);
    await waitForElement(
      wrapper,
      'HostsList',
      el => el.state('hasContentLoading') === true
    );
    expect(loadHosts).toHaveBeenCalled();
    await waitForElement(
      wrapper,
      'HostsList',
      el => el.state('hasContentLoading') === false
    );
    done();
  });

  test('handleSelect is called when a host list item is selected', async done => {
    const handleSelect = jest.spyOn(_HostsList.prototype, 'handleSelect');
    const wrapper = mountWithContexts(<HostsList />);
    await waitForElement(
      wrapper,
      'HostsList',
      el => el.state('hasContentLoading') === false
    );
    await wrapper
      .find('input#select-host-1')
      .closest('DataListCheck')
      .props()
      .onChange();
    expect(handleSelect).toBeCalled();
    await waitForElement(
      wrapper,
      'HostsList',
      el => el.state('selected').length === 1
    );
    done();
  });

  test('handleSelectAll is called when select all checkbox is clicked', async done => {
    const handleSelectAll = jest.spyOn(_HostsList.prototype, 'handleSelectAll');
    const wrapper = mountWithContexts(<HostsList />);
    await waitForElement(
      wrapper,
      'HostsList',
      el => el.state('hasContentLoading') === false
    );
    wrapper
      .find('Checkbox#select-all')
      .props()
      .onChange(true);
    expect(handleSelectAll).toBeCalled();
    await waitForElement(
      wrapper,
      'HostsList',
      el => el.state('selected').length === 3
    );
    done();
  });

  test('delete button is disabled if user does not have delete capabilities on a selected host', async done => {
    const wrapper = mountWithContexts(<HostsList />);
    wrapper.find('HostsList').setState({
      hosts: mockHosts,
      itemCount: 3,
      isInitialized: true,
      selected: mockHosts.slice(0, 1),
    });
    await waitForElement(
      wrapper,
      'ToolbarDeleteButton * button',
      el => el.getDOMNode().disabled === false
    );
    wrapper.find('HostsList').setState({
      selected: mockHosts,
    });
    await waitForElement(
      wrapper,
      'ToolbarDeleteButton * button',
      el => el.getDOMNode().disabled === true
    );
    done();
  });

  test('api is called to delete hosts for each selected host.', () => {
    HostsAPI.destroy = jest.fn();
    const wrapper = mountWithContexts(<HostsList />);
    wrapper.find('HostsList').setState({
      hosts: mockHosts,
      itemCount: 2,
      isInitialized: true,
      isModalOpen: true,
      selected: mockHosts.slice(0, 2),
    });
    wrapper.find('ToolbarDeleteButton').prop('onDelete')();
    expect(HostsAPI.destroy).toHaveBeenCalledTimes(2);
  });

  test('error is shown when host not successfully deleted from api', async done => {
    HostsAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/hosts/1',
          },
          data: 'An error occurred',
        },
      })
    );
    const wrapper = mountWithContexts(<HostsList />);
    wrapper.find('HostsList').setState({
      hosts: mockHosts,
      itemCount: 1,
      isInitialized: true,
      isModalOpen: true,
      selected: mockHosts.slice(0, 1),
    });
    wrapper.find('ToolbarDeleteButton').prop('onDelete')();
    await sleep(0);
    wrapper.update();
    await waitForElement(
      wrapper,
      'Modal',
      el => el.props().isOpen === true && el.props().title === 'Error!'
    );

    done();
  });

  test('Add button shown for users without ability to POST', async done => {
    const wrapper = mountWithContexts(<HostsList />);
    await waitForElement(
      wrapper,
      'HostsList',
      el => el.state('hasContentLoading') === true
    );
    await waitForElement(
      wrapper,
      'HostsList',
      el => el.state('hasContentLoading') === false
    );
    expect(wrapper.find('ToolbarAddButton').length).toBe(1);
    done();
  });

  test('Add button hidden for users without ability to POST', async done => {
    HostsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
        },
      },
    });
    const wrapper = mountWithContexts(<HostsList />);
    await waitForElement(
      wrapper,
      'HostsList',
      el => el.state('hasContentLoading') === true
    );
    await waitForElement(
      wrapper,
      'HostsList',
      el => el.state('hasContentLoading') === false
    );
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
    done();
  });
});
