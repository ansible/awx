import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import SmartInventoryAdd from './SmartInventoryAdd';
import {
  InventoriesAPI,
  OrganizationsAPI,
  InstanceGroupsAPI,
} from '../../../api';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 1,
  }),
}));

jest.mock('../../../api/models/Inventories');
jest.mock('../../../api/models/Organizations');
jest.mock('../../../api/models/InstanceGroups');
OrganizationsAPI.read.mockResolvedValue({ data: { results: [], count: 0 } });
InstanceGroupsAPI.read.mockResolvedValue({ data: { results: [], count: 0 } });

const formData = {
  name: 'Mock',
  description: 'Foo',
  organization: { id: 1 },
  kind: 'smart',
  host_filter: 'name__icontains=mock',
  variables: '---',
  instance_groups: [{ id: 2 }],
};

describe('<SmartInventoryAdd />', () => {
  describe('when initialized by users with POST capability', () => {
    let history;
    let wrapper;

    beforeAll(async () => {
      InventoriesAPI.create.mockResolvedValueOnce({ data: { id: 1 } });
      InventoriesAPI.readOptions.mockResolvedValue({
        data: { actions: { POST: true } },
      });
      history = createMemoryHistory({
        initialEntries: [`/inventories/smart_inventory/add`],
      });
      await act(async () => {
        wrapper = mountWithContexts(<SmartInventoryAdd />, {
          context: { router: { history } },
        });
      });
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    });

    afterAll(() => {
      jest.clearAllMocks();
      wrapper.unmount();
    });

    test('should enable save button', () => {
      expect(wrapper.find('Button[aria-label="Save"]').prop('isDisabled')).toBe(
        false
      );
    });

    test('should post to the api when submit is clicked', async () => {
      await act(async () => {
        wrapper.find('SmartInventoryForm').invoke('onSubmit')(formData);
      });
      const { instance_groups, ...formRequest } = formData;
      expect(InventoriesAPI.create).toHaveBeenCalledTimes(1);
      expect(InventoriesAPI.create).toHaveBeenCalledWith({
        ...formRequest,
        organization: formRequest.organization.id,
      });
      expect(InventoriesAPI.associateInstanceGroup).toHaveBeenCalledTimes(1);
      expect(InventoriesAPI.associateInstanceGroup).toHaveBeenCalledWith(1, 2);
    });

    test('successful form submission should trigger redirect to details', async () => {
      expect(history.location.pathname).toEqual(
        '/inventories/smart_inventory/1/details'
      );
    });

    test('should navigate to inventory list when cancel is clicked', async () => {
      await act(async () => {
        wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
      });
      expect(history.location.pathname).toEqual('/inventories');
    });

    test('unsuccessful form submission should show an error message', async () => {
      const error = {
        response: {
          data: { detail: 'An error occurred' },
        },
      };
      InventoriesAPI.create.mockImplementationOnce(() => Promise.reject(error));
      await act(async () => {
        wrapper = mountWithContexts(<SmartInventoryAdd />);
      });
      expect(wrapper.find('FormSubmitError').length).toBe(0);
      await act(async () => {
        wrapper.find('SmartInventoryForm').invoke('onSubmit')({});
      });
      wrapper.update();
      expect(wrapper.find('FormSubmitError').length).toBe(1);
    });
  });

  describe('when initialized by users without POST capability', () => {
    let wrapper;

    beforeAll(async () => {
      InventoriesAPI.readOptions.mockResolvedValueOnce({
        data: { actions: { POST: false } },
      });
      await act(async () => {
        wrapper = mountWithContexts(<SmartInventoryAdd />);
      });
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    });
    afterAll(() => {
      jest.clearAllMocks();
      wrapper.unmount();
    });

    test('should disable save button', () => {
      expect(wrapper.find('Button[aria-label="Save"]').prop('isDisabled')).toBe(
        true
      );
    });
  });
});
