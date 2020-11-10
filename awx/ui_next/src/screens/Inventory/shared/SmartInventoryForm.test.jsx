import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import SmartInventoryForm from './SmartInventoryForm';
import {
  InventoriesAPI,
  OrganizationsAPI,
  InstanceGroupsAPI,
} from '../../../api';

jest.mock('../../../api/models/Inventories');
jest.mock('../../../api/models/Organizations');
jest.mock('../../../api/models/InstanceGroups');
OrganizationsAPI.read.mockResolvedValue({ data: { results: [], count: 0 } });
InstanceGroupsAPI.read.mockResolvedValue({ data: { results: [], count: 0 } });
InventoriesAPI.readOptions.mockResolvedValue({
  data: { actions: { POST: true } },
});

const mockFormValues = {
  kind: 'smart',
  name: 'new smart inventory',
  description: '',
  organization: { id: 1, name: 'mock organization' },
  host_filter:
    'name__icontains=mock and name__icontains=foo and groups__name__icontains=mock group',
  instance_groups: [{ id: 123 }],
  variables: '---',
};

describe('<SmartInventoryForm />', () => {
  describe('when initialized by users with POST capability', () => {
    let wrapper;
    const onSubmit = jest.fn();

    beforeAll(async () => {
      await act(async () => {
        wrapper = mountWithContexts(
          <SmartInventoryForm onCancel={() => {}} onSubmit={onSubmit} />
        );
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

    test('should show expected form fields', () => {
      expect(wrapper.find('FormGroup[label="Name"]')).toHaveLength(1);
      expect(wrapper.find('FormGroup[label="Description"]')).toHaveLength(1);
      expect(wrapper.find('FormGroup[label="Organization"]')).toHaveLength(1);
      expect(wrapper.find('FormGroup[label="Host filter"]')).toHaveLength(1);
      expect(wrapper.find('FormGroup[label="Instance Groups"]')).toHaveLength(
        1
      );
      expect(wrapper.find('VariablesField[label="Variables"]')).toHaveLength(1);
      expect(wrapper.find('Button[aria-label="Save"]')).toHaveLength(1);
      expect(wrapper.find('Button[aria-label="Cancel"]')).toHaveLength(1);
    });

    test('should enable host filter field when organization field has a value', async () => {
      expect(wrapper.find('HostFilterLookup').prop('isDisabled')).toBe(true);
      await act(async () => {
        wrapper.find('OrganizationLookup').invoke('onBlur')();
        wrapper.find('OrganizationLookup').invoke('onChange')(
          mockFormValues.organization
        );
      });
      wrapper.update();
      expect(wrapper.find('HostFilterLookup').prop('isDisabled')).toBe(false);
    });

    test('should show error when form is saved without a host filter value', async () => {
      expect(wrapper.find('HostFilterLookup #host-filter-helper').length).toBe(
        0
      );
      wrapper.find('input#name').simulate('change', {
        target: { value: mockFormValues.name, name: 'name' },
      });
      await act(async () => {
        wrapper.find('button[aria-label="Save"]').simulate('click');
      });
      wrapper.update();
      const hostFilterError = wrapper.find(
        'HostFilterLookup #host-filter-helper'
      );
      expect(hostFilterError.length).toBe(1);
      expect(hostFilterError.text()).toContain('This field must not be blank');
      expect(onSubmit).not.toHaveBeenCalled();
    });

    test('should display filter chips when host filter has a value', async () => {
      await act(async () => {
        wrapper.find('HostFilterLookup').invoke('onBlur')();
        wrapper.find('HostFilterLookup').invoke('onChange')(
          mockFormValues.host_filter
        );
      });
      wrapper.update();
      const nameChipGroup = wrapper.find(
        'HostFilterLookup ChipGroup[categoryName="Name"]'
      );
      const groupChipGroup = wrapper.find(
        'HostFilterLookup ChipGroup[categoryName="Group"]'
      );
      expect(nameChipGroup.find('Chip').length).toBe(2);
      expect(groupChipGroup.find('Chip').length).toBe(1);
    });

    test('should submit expected form values on save', async () => {
      await act(async () => {
        wrapper.find('InstanceGroupsLookup').invoke('onChange')(
          mockFormValues.instance_groups
        );
      });
      wrapper.update();
      await act(async () => {
        wrapper.find('button[aria-label="Save"]').simulate('click');
      });
      wrapper.update();
      expect(onSubmit).toHaveBeenCalledWith(mockFormValues);
    });
  });

  test('should throw content error when option request fails', async () => {
    let wrapper;
    InventoriesAPI.readOptions.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <SmartInventoryForm onCancel={() => {}} onSubmit={() => {}} />
      );
    });
    expect(wrapper.find('ContentError').length).toBe(0);
    wrapper.update();
    expect(wrapper.find('ContentError').length).toBe(1);
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should throw content error when option request fails', async () => {
    let wrapper;
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    await act(async () => {
      wrapper = mountWithContexts(
        <SmartInventoryForm
          submitError={error}
          onCancel={() => {}}
          onSubmit={() => {}}
        />
      );
    });
    expect(wrapper.find('FormSubmitError').length).toBe(1);
    expect(wrapper.find('SmartInventoryForm').prop('submitError')).toEqual(
      error
    );
    wrapper.unmount();
    jest.clearAllMocks();
  });
});
