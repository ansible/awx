import React from 'react';
import { act } from 'react-dom/test-utils';
import { HostsAPI } from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';

import HostList, { _HostList } from './HostList';

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
      recent_jobs: [],
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
      recent_jobs: [],
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
      recent_jobs: [
        {
          id: 123,
          name: 'Bibbity Bop',
          status: 'success',
          finished: '2020-01-27T19:40:36.208728Z',
        },
      ],
      user_capabilities: {
        delete: false,
        update: false,
      },
    },
  },
];

function waitForLoaded(wrapper) {
  return waitForElement(
    wrapper,
    'HostList',
    el => el.find('ContentLoading').length === 0
  );
}

describe('<HostList />', () => {
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

  test('initially renders successfully', async () => {
    await act(async () => {
      mountWithContexts(
        <HostList
          match={{ path: '/hosts', url: '/hosts' }}
          location={{ search: '', pathname: '/hosts' }}
        />
      );
    });
  });

  test.only('Hosts are retrieved from the api and the components finishes loading', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<HostList />);
    });
    await waitForLoaded(wrapper);
    expect(HostsAPI.read).toHaveBeenCalled();
    expect(wrapper.find('HostListItem')).toHaveLength(3);
  });

  test('handleSelect is called when a host list item is selected', async () => {
    const handleSelect = jest.spyOn(_HostList.prototype, 'handleSelect');
    const wrapper = mountWithContexts(<HostList />);
    await waitForElement(
      wrapper,
      'HostList',
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
      'HostList',
      el => el.state('selected').length === 1
    );
  });

  test('handleSelectAll is called when select all checkbox is clicked', async () => {
    const handleSelectAll = jest.spyOn(_HostList.prototype, 'handleSelectAll');
    const wrapper = mountWithContexts(<HostList />);
    await waitForElement(
      wrapper,
      'HostList',
      el => el.state('hasContentLoading') === false
    );
    wrapper
      .find('Checkbox#select-all')
      .props()
      .onChange(true);
    expect(handleSelectAll).toBeCalled();
    await waitForElement(
      wrapper,
      'HostList',
      el => el.state('selected').length === 3
    );
  });

  test('delete button is disabled if user does not have delete capabilities on a selected host', async () => {
    const wrapper = mountWithContexts(<HostList />);
    wrapper.find('HostList').setState({
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
    wrapper.find('HostList').setState({
      selected: mockHosts,
    });
    await waitForElement(
      wrapper,
      'ToolbarDeleteButton * button',
      el => el.getDOMNode().disabled === true
    );
  });

  test('api is called to delete hosts for each selected host.', () => {
    HostsAPI.destroy = jest.fn();
    const wrapper = mountWithContexts(<HostList />);
    wrapper.find('HostList').setState({
      hosts: mockHosts,
      itemCount: 2,
      isInitialized: true,
      isModalOpen: true,
      selected: mockHosts.slice(0, 2),
    });
    wrapper.find('ToolbarDeleteButton').prop('onDelete')();
    expect(HostsAPI.destroy).toHaveBeenCalledTimes(2);
  });

  test('error is shown when host not successfully deleted from api', async () => {
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
    const wrapper = mountWithContexts(<HostList />);
    wrapper.find('HostList').setState({
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
  });

  test('Add button shown for users without ability to POST', async () => {
    const wrapper = mountWithContexts(<HostList />);
    await waitForElement(
      wrapper,
      'HostList',
      el => el.state('hasContentLoading') === true
    );
    await waitForElement(
      wrapper,
      'HostList',
      el => el.state('hasContentLoading') === false
    );
    expect(wrapper.find('ToolbarAddButton').length).toBe(1);
  });

  test('Add button hidden for users without ability to POST', async () => {
    HostsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
        },
      },
    });
    const wrapper = mountWithContexts(<HostList />);
    await waitForElement(
      wrapper,
      'HostList',
      el => el.state('hasContentLoading') === true
    );
    await waitForElement(
      wrapper,
      'HostList',
      el => el.state('hasContentLoading') === false
    );
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
  });
});
