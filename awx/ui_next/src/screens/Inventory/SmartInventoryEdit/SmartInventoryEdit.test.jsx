import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import SmartInventoryEdit from './SmartInventoryEdit';
import mockSmartInventory from '../shared/data.smart_inventory.json';
import {
  InventoriesAPI,
  OrganizationsAPI,
  InstanceGroupsAPI,
} from '../../../api';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 2,
  }),
}));
jest.mock('../../../api/models/Inventories');
jest.mock('../../../api/models/Organizations');
jest.mock('../../../api/models/InstanceGroups');
OrganizationsAPI.read.mockResolvedValue({ data: { results: [], count: 0 } });
InstanceGroupsAPI.read.mockResolvedValue({ data: { results: [], count: 0 } });

const mockSmartInv = Object.assign(
  {},
  {
    ...mockSmartInventory,
    organization: {
      id: mockSmartInventory.organization,
    },
  }
);

describe('<SmartInventoryEdit />', () => {
  let history;
  let wrapper;

  beforeAll(async () => {
    InventoriesAPI.associateInstanceGroup.mockResolvedValue();
    InventoriesAPI.disassociateInstanceGroup.mockResolvedValue();
    InventoriesAPI.update.mockResolvedValue({ data: mockSmartInv });
    InventoriesAPI.readOptions.mockResolvedValue({
      data: { actions: { POST: true } },
    });
    InventoriesAPI.readInstanceGroups.mockResolvedValue({
      data: { count: 0, results: [{ id: 10 }, { id: 20 }] },
    });
    history = createMemoryHistory({
      initialEntries: [`/inventories/smart_inventory/${mockSmartInv.id}/edit`],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SmartInventoryEdit inventory={{ ...mockSmartInv }} />,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  afterAll(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('should fetch related instance groups on initial render', async () => {
    expect(InventoriesAPI.readInstanceGroups).toHaveBeenCalledTimes(1);
  });

  test('save button should be enabled for users with POST capability', () => {
    expect(wrapper.find('Button[aria-label="Save"]').prop('isDisabled')).toBe(
      false
    );
  });

  test('should post to the api when submit is clicked', async () => {
    expect(InventoriesAPI.update).toHaveBeenCalledTimes(0);
    expect(InventoriesAPI.associateInstanceGroup).toHaveBeenCalledTimes(0);
    expect(InventoriesAPI.disassociateInstanceGroup).toHaveBeenCalledTimes(0);
    await act(async () => {
      wrapper.find('SmartInventoryForm').invoke('onSubmit')({
        ...mockSmartInv,
        instance_groups: [{ id: 10 }, { id: 30 }],
      });
    });
    expect(InventoriesAPI.update).toHaveBeenCalledTimes(1);
    expect(InventoriesAPI.associateInstanceGroup).toHaveBeenCalledTimes(1);
    expect(InventoriesAPI.disassociateInstanceGroup).toHaveBeenCalledTimes(1);
  });

  test('successful form submission should trigger redirect to details', async () => {
    expect(wrapper.find('FormSubmitError').length).toBe(0);
    expect(history.location.pathname).toEqual(
      '/inventories/smart_inventory/2/details'
    );
  });

  test('should navigate to inventory details when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual(
      '/inventories/smart_inventory/2/details'
    );
  });

  test('unsuccessful form submission should show an error message', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    InventoriesAPI.update.mockImplementationOnce(() => Promise.reject(error));
    await act(async () => {
      wrapper = mountWithContexts(
        <SmartInventoryEdit inventory={{ ...mockSmartInv }} />
      );
    });
    expect(wrapper.find('FormSubmitError').length).toBe(0);
    await act(async () => {
      wrapper.find('SmartInventoryForm').invoke('onSubmit')({});
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
  });

  test('should throw content error', async () => {
    expect(wrapper.find('ContentError').length).toBe(0);
    InventoriesAPI.readInstanceGroups.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <SmartInventoryEdit inventory={{ ...mockSmartInv }} />
      );
    });
    wrapper.update();
    expect(wrapper.find('ContentError').length).toBe(1);
  });

  test('save button should be disabled for users without POST capability', async () => {
    InventoriesAPI.readOptions.mockResolvedValue({
      data: { actions: { POST: false } },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SmartInventoryEdit inventory={{ ...mockSmartInv }} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('Button[aria-label="Save"]').prop('isDisabled')).toBe(
      true
    );
  });
});
