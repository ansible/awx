import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { InventoriesAPI, OrganizationsAPI, InstanceGroupsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import SmartInventoryAdd from './SmartInventoryAdd';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 1,
  }),
}));

jest.mock('../../../api');

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
  const history = createMemoryHistory({
    initialEntries: [`/inventories/smart_inventory/add`],
  });

  describe('when initialized by users with POST capability', () => {
    let wrapper;
    let consoleError;

    beforeAll(() => {
      consoleError = global.console.error;
      global.console.error = jest.fn();
    });

    beforeEach(async () => {
      OrganizationsAPI.read.mockResolvedValue({
        data: { results: [], count: 0 },
      });
      InstanceGroupsAPI.read.mockResolvedValue({
        data: { results: [], count: 0 },
      });
      InventoriesAPI.create.mockResolvedValueOnce({ data: { id: 1 } });
      InventoriesAPI.readOptions.mockResolvedValue({
        data: { actions: { POST: true } },
      });
      InstanceGroupsAPI.read.mockResolvedValue({
        data: { results: [], count: 0 },
      });

      await act(async () => {
        wrapper = mountWithContexts(<SmartInventoryAdd />, {
          context: { router: { history } },
        });
      });
      await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    });

    afterAll(() => {
      global.console.error = consoleError;
      jest.clearAllMocks();
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

    test('should parse host_filter with ansible facts', async () => {
      const modifiedForm = {
        ...formData,
        host_filter:
          'host_filter=ansible_facts__ansible_env__PYTHONUNBUFFERED="true"',
      };
      await act(async () => {
        wrapper.find('SmartInventoryForm').invoke('onSubmit')(modifiedForm);
      });
      const { instance_groups, ...formRequest } = modifiedForm;
      expect(InventoriesAPI.create).toHaveBeenCalledTimes(1);
      expect(InventoriesAPI.create).toHaveBeenCalledWith({
        ...formRequest,
        organization: formRequest.organization.id,
        host_filter: 'ansible_facts__ansible_env__PYTHONUNBUFFERED="true"',
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

    afterAll(() => {
      jest.clearAllMocks();
    });

    beforeEach(async () => {
      OrganizationsAPI.read.mockResolvedValue({
        data: { results: [], count: 0 },
      });
      InstanceGroupsAPI.read.mockResolvedValue({
        data: { results: [], count: 0 },
      });
      InventoriesAPI.create.mockResolvedValueOnce({ data: { id: 1 } });
      InventoriesAPI.readOptions.mockResolvedValue({
        data: { actions: { POST: false } },
      });
      InstanceGroupsAPI.read.mockResolvedValue({
        data: { results: [], count: 0 },
      });

      await act(async () => {
        wrapper = mountWithContexts(<SmartInventoryAdd />, {
          context: { router: { history } },
        });
      });
      await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    });

    test('should disable save button', () => {
      expect(wrapper.find('Button[aria-label="Save"]').prop('isDisabled')).toBe(
        true
      );
    });
  });
});
