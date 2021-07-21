import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { InventoriesAPI, OrganizationsAPI, InstanceGroupsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import SmartInventoryForm from './SmartInventoryForm';

jest.mock('../../../api');

const mockFormValues = {
  kind: 'smart',
  name: 'new smart inventory',
  description: '',
  organization: { id: 1, name: 'mock organization' },
  host_filter:
    'name__icontains=mock and name__icontains=foo and groups__name__icontains=mock group',
  instance_groups: [{ id: 123, name: 'mock instance group' }],
  variables: '---',
};

describe('<SmartInventoryForm />', () => {
  let wrapper;
  const onSubmit = jest.fn();

  beforeAll(async () => {
    OrganizationsAPI.read.mockResolvedValue({
      data: { results: [], count: 0 },
    });
    InstanceGroupsAPI.read.mockResolvedValue({
      data: { results: [], count: 0 },
    });
    InventoriesAPI.readOptions.mockResolvedValue({
      data: { actions: { POST: true } },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SmartInventoryForm onCancel={() => {}} onSubmit={onSubmit} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  afterAll(() => {
    jest.clearAllMocks();
  });

  describe('when initialized by users with POST capability', () => {
    test('should enable save button', () => {
      expect(wrapper.find('Button[aria-label="Save"]').prop('isDisabled')).toBe(
        false
      );
    });

    test('should show expected form fields', () => {
      expect(wrapper.find('FormGroup[label="Name"]')).toHaveLength(1);
      expect(wrapper.find('FormGroup[label="Description"]')).toHaveLength(1);
      expect(wrapper.find('FormGroup[label="Organization"]')).toHaveLength(1);
      expect(wrapper.find('FormGroup[label="Smart host filter"]')).toHaveLength(
        1
      );
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

    test('should display filter chips for advanced host filter', async () => {
      await act(async () => {
        wrapper.find('HostFilterLookup').invoke('onBlur')();
        wrapper.find('HostFilterLookup').invoke('onChange')(
          'name__contains=f or name__contains=o'
        );
      });
      wrapper.update();
      const nameChipGroup = wrapper.find(
        'HostFilterLookup ChipGroup[categoryName="name__contains"]'
      );
      expect(nameChipGroup.find('Chip').length).toBe(2);
      expect(nameChipGroup.find('Chip').at(0).prop('children')).toBe('f');
      expect(nameChipGroup.find('Chip').at(1).prop('children')).toBe('o');
    });

    test('should submit expected form values on save', async () => {
      await act(async () => {
        wrapper.find('InstanceGroupsLookup').invoke('onChange')(
          mockFormValues.instance_groups
        );
      });
      await act(async () => {
        wrapper.find('HostFilterLookup').invoke('onBlur')();
        wrapper.find('HostFilterLookup').invoke('onChange')(
          mockFormValues.host_filter
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

  test('should pre-fill the host filter when query param present and not editing', async () => {
    InventoriesAPI.readOptions.mockResolvedValue({
      data: { actions: { POST: true } },
    });
    let newWrapper;
    const history = createMemoryHistory({
      initialEntries: [
        '/inventories/smart_inventory/add?host_filter=name__icontains%3Dfoo',
      ],
    });
    await act(async () => {
      newWrapper = mountWithContexts(
        <SmartInventoryForm onCancel={() => {}} onSubmit={() => {}} />,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(newWrapper, 'ContentLoading', (el) => el.length === 0);
    newWrapper.update();
    const nameChipGroup = newWrapper.find(
      'HostFilterLookup ChipGroup[categoryName="Name"]'
    );
    expect(nameChipGroup.find('Chip').length).toBe(1);
  });

  test('should throw content error when option request fails', async () => {
    let newWrapper;
    InventoriesAPI.readOptions.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      newWrapper = mountWithContexts(
        <SmartInventoryForm onCancel={() => {}} onSubmit={() => {}} />
      );
    });
    expect(newWrapper.find('ContentError').length).toBe(0);
    newWrapper.update();
    expect(newWrapper.find('ContentError').length).toBe(1);
    jest.clearAllMocks();
  });

  test('should throw content error when option request fails', async () => {
    let newWrapper;
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    await act(async () => {
      newWrapper = mountWithContexts(
        <SmartInventoryForm
          submitError={error}
          onCancel={() => {}}
          onSubmit={() => {}}
        />
      );
    });
    expect(newWrapper.find('FormSubmitError').length).toBe(1);
    expect(newWrapper.find('SmartInventoryForm').prop('submitError')).toEqual(
      error
    );
    jest.clearAllMocks();
  });
});
