import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { HostsAPI } from '../../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import HostList from './HostList';

jest.mock('../../../api');

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

  test('Hosts are retrieved from the api and the components finishes loading', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<HostList />);
    });
    await waitForLoaded(wrapper);

    expect(HostsAPI.read).toHaveBeenCalled();
    expect(wrapper.find('HostListItem')).toHaveLength(3);
  });

  test('should select and deselect a single item', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<HostList />);
    });
    await waitForLoaded(wrapper);

    act(() => {
      wrapper
        .find('.pf-c-table__check')
        .first()
        .find('input')
        .invoke('onChange')();
    });
    wrapper.update();
    expect(
      wrapper
        .find('HostListItem')
        .first()
        .prop('isSelected')
    ).toEqual(true);
    act(() => {
      wrapper
        .find('.pf-c-table__check')
        .first()
        .find('input')
        .invoke('onChange')();
    });
    wrapper.update();
    expect(
      wrapper
        .find('HostListItem')
        .first()
        .prop('isSelected')
    ).toEqual(false);
  });

  test('should select all items', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<HostList />);
    });
    await waitForLoaded(wrapper);

    act(() => {
      wrapper.find('DataListToolbar').invoke('onSelectAll')(true);
    });
    wrapper.update();

    wrapper.find('HostListItem').forEach(item => {
      expect(item.prop('isSelected')).toEqual(true);
    });
  });

  test('delete button is disabled if user does not have delete capabilities on a selected host', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<HostList />);
    });
    await waitForLoaded(wrapper);

    act(() => {
      wrapper
        .find('HostListItem')
        .at(2)
        .invoke('onSelect')();
    });
    expect(wrapper.find('ToolbarDeleteButton button').prop('disabled')).toEqual(
      true
    );
  });

  test('api is called to delete hosts for each selected host.', async () => {
    HostsAPI.destroy = jest.fn();
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<HostList />);
    });
    await waitForLoaded(wrapper);

    await act(async () => {
      wrapper
        .find('HostListItem')
        .at(0)
        .invoke('onSelect')();
    });
    wrapper.update();
    await act(async () => {
      wrapper
        .find('HostListItem')
        .at(1)
        .invoke('onSelect')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });
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
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<HostList />);
    });
    await waitForLoaded(wrapper);

    await act(async () => {
      wrapper
        .find('HostListItem')
        .at(0)
        .invoke('onSelect')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('ToolbarDeleteButton').invoke('onDelete')();
    });
    wrapper.update();

    const modal = wrapper.find('Modal');
    expect(modal).toHaveLength(1);
    expect(modal.prop('title')).toEqual('Error!');
  });

  test('should show Add and Smart Inventory buttons according to permissions', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<HostList />);
    });
    await waitForLoaded(wrapper);

    expect(wrapper.find('ToolbarAddButton').length).toBe(1);
    expect(wrapper.find('Button[aria-label="Smart Inventory"]').length).toBe(1);
  });

  test('should hide Add and Smart Inventory buttons according to permissions', async () => {
    HostsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
        },
      },
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<HostList />);
    });
    await waitForLoaded(wrapper);

    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
    expect(wrapper.find('Button[aria-label="Smart Inventory"]').length).toBe(0);
  });

  test('Smart Inventory button should be disabled when no search params are present', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<HostList />);
    });
    await waitForLoaded(wrapper);
    expect(
      wrapper.find('Button[aria-label="Smart Inventory"]').props().isDisabled
    ).toBe(true);
  });

  test('Clicking Smart Inventory button should navigate to smart inventory form with correct query param', async () => {
    let wrapper;
    const history = createMemoryHistory({
      initialEntries: ['/hosts?host.name__icontains=foo'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<HostList />, {
        context: { router: { history } },
      });
    });

    await waitForLoaded(wrapper);
    expect(
      wrapper.find('Button[aria-label="Smart Inventory"]').props().isDisabled
    ).toBe(false);
    await act(async () => {
      wrapper.find('Button[aria-label="Smart Inventory"]').simulate('click');
    });
    wrapper.update();
    expect(history.location.pathname).toEqual(
      '/inventories/smart_inventory/add'
    );
    expect(history.location.search).toEqual(
      '?host_filter=name__icontains%3Dfoo'
    );
  });
});
