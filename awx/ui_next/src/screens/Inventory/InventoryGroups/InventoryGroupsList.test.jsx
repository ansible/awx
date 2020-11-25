import React from 'react';
import { act } from 'react-dom/test-utils';
import { Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import { InventoriesAPI, GroupsAPI } from '../../../api';
import InventoryGroupsList from './InventoryGroupsList';

jest.mock('../../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 1,
  }),
}));
const mockGroups = [
  {
    id: 1,
    type: 'group',
    name: 'foo',
    inventory: 1,
    url: '/api/v2/groups/1',
    summary_fields: {
      user_capabilities: {
        delete: true,
        edit: true,
      },
    },
  },
  {
    id: 2,
    type: 'group',
    name: 'bar',
    inventory: 1,
    url: '/api/v2/groups/2',
    summary_fields: {
      user_capabilities: {
        delete: true,
        edit: true,
      },
    },
  },
  {
    id: 3,
    type: 'group',
    name: 'baz',
    inventory: 1,
    url: '/api/v2/groups/3',
    summary_fields: {
      user_capabilities: {
        delete: false,
        edit: false,
      },
    },
  },
];

describe('<InventoryGroupsList />', () => {
  let wrapper;

  beforeEach(async () => {
    InventoriesAPI.readGroups.mockResolvedValue({
      data: {
        count: mockGroups.length,
        results: mockGroups,
      },
    });
    InventoriesAPI.readGroupsOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
      },
    });
    const history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/3/groups'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route path="/inventories/inventory/:id/groups">
          <InventoryGroupsList />
        </Route>,
        {
          context: {
            router: { history, route: { location: history.location } },
          },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });
  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('initially renders successfully', () => {
    expect(wrapper.find('InventoryGroupsList').length).toBe(1);
  });

  test('should fetch groups from api and render them in the list', async () => {
    expect(InventoriesAPI.readGroups).toHaveBeenCalled();
    expect(wrapper.find('InventoryGroupItem').length).toBe(3);
  });

  test('should check and uncheck the row item', async () => {
    expect(
      wrapper.find('DataListCheck[id="select-group-1"]').props().checked
    ).toBe(false);

    await act(async () => {
      wrapper.find('DataListCheck[id="select-group-1"]').invoke('onChange')(
        true
      );
    });
    wrapper.update();
    expect(
      wrapper.find('DataListCheck[id="select-group-1"]').props().checked
    ).toBe(true);

    await act(async () => {
      wrapper.find('DataListCheck[id="select-group-1"]').invoke('onChange')(
        false
      );
    });
    wrapper.update();
    expect(
      wrapper.find('DataListCheck[id="select-group-1"]').props().checked
    ).toBe(false);
  });

  test('should check all row items when select all is checked', async () => {
    wrapper.find('DataListCheck').forEach(el => {
      expect(el.props().checked).toBe(false);
    });
    await act(async () => {
      wrapper.find('Checkbox#select-all').invoke('onChange')(true);
    });
    wrapper.update();
    wrapper.find('DataListCheck').forEach(el => {
      expect(el.props().checked).toBe(true);
    });
    await act(async () => {
      wrapper.find('Checkbox#select-all').invoke('onChange')(false);
    });
    wrapper.update();
    wrapper.find('DataListCheck').forEach(el => {
      expect(el.props().checked).toBe(false);
    });
  });
});
describe('<InventoryGroupsList/> error handling', () => {
  let wrapper;
  beforeEach(() => {
    InventoriesAPI.readGroups.mockResolvedValue({
      data: {
        count: mockGroups.length,
        results: mockGroups,
      },
    });
    InventoriesAPI.readGroupsOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
      },
    });
    GroupsAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/groups/1',
          },
          data: 'An error occurred',
        },
      })
    );
  });
  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });
  test('should show content error when api throws error on initial render', async () => {
    InventoriesAPI.readGroupsOptions.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(<InventoryGroupsList />);
    });
    await waitForElement(wrapper, 'ContentError', el => el.length > 0);
  });

  test('should show content error if groups are not successfully fetched from api', async () => {
    InventoriesAPI.readGroups.mockImplementation(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(<InventoryGroupsList />);
    });
    await waitForElement(wrapper, 'ContentError', el => el.length > 0);
  });

  test('should show error modal when group is not successfully deleted from api', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<InventoryGroupsList />);
    });
    waitForElement(wrapper, 'ContentEmpty', el => el.length === 0);

    await act(async () => {
      wrapper.find('DataListCheck[id="select-group-1"]').invoke('onChange')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('Toolbar Button[aria-label="Delete"]').invoke('onClick')();
    });
    await waitForElement(
      wrapper,
      'AlertModal[title="Delete Group?"]',
      el => el.props().isOpen === true
    );
    await act(async () => {
      wrapper.find('Radio[id="radio-delete"]').invoke('onChange')();
    });
    wrapper.update();
    await act(async () => {
      wrapper
        .find('ModalBoxFooter Button[aria-label="Confirm Delete"]')
        .invoke('onClick')();
    });
    await waitForElement(
      wrapper,
      'AlertModal[aria-label="deletion error"] Modal',
      el => el.props().isOpen === true && el.props().title === 'Error!'
    );

    await act(async () => {
      wrapper
        .find('AlertModal[aria-label="deletion error"]')
        .invoke('onClose')();
    });
  });
});
