import React from 'react';
import { act } from 'react-dom/test-utils';
import { ConstructedInventoriesAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import ConstructedInventoryForm from './ConstructedInventoryForm';

jest.mock('../../../api');

const mockFormValues = {
  kind: 'constructed',
  name: 'new constructed inventory',
  description: '',
  organization: { id: 1, name: 'mock organization' },
  instanceGroups: [],
  source_vars: 'plugin: constructed',
  inputInventories: [{ id: 100, name: 'East' }],
};

describe('<ConstructedInventoryForm />', () => {
  let wrapper;
  const onSubmit = jest.fn();

  beforeEach(async () => {
    ConstructedInventoriesAPI.readOptions.mockResolvedValue({
      data: {
        related: {},
        actions: {
          POST: {
            limit: {
              label: 'Limit',
              help_text: '',
            },
            update_cache_timeout: {
              label: 'Update cache timeout',
              help_text: 'help',
            },
            verbosity: {
              label: 'Verbosity',
              help_text: '',
            },
          },
        },
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <ConstructedInventoryForm onCancel={() => {}} onSubmit={onSubmit} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  test('should show expected form fields', () => {
    expect(wrapper.find('FormGroup[label="Name"]')).toHaveLength(1);
    expect(wrapper.find('FormGroup[label="Description"]')).toHaveLength(1);
    expect(wrapper.find('FormGroup[label="Organization"]')).toHaveLength(1);
    expect(wrapper.find('FormGroup[label="Instance Groups"]')).toHaveLength(1);
    expect(wrapper.find('FormGroup[label="Input Inventories"]')).toHaveLength(
      1
    );
    expect(
      wrapper.find('FormGroup[label="Cache timeout (seconds)"]')
    ).toHaveLength(1);
    expect(wrapper.find('FormGroup[label="Verbosity"]')).toHaveLength(1);
    expect(wrapper.find('FormGroup[label="Limit"]')).toHaveLength(1);
    expect(wrapper.find('VariablesField[label="Source vars"]')).toHaveLength(1);
    expect(wrapper.find('ConstructedInventoryHint')).toHaveLength(1);
    expect(wrapper.find('Button[aria-label="Save"]')).toHaveLength(1);
    expect(wrapper.find('Button[aria-label="Cancel"]')).toHaveLength(1);
  });

  test('should show field error when form is saved without a input inventories', async () => {
    const inventoryErrorHelper = 'div#input-inventories-lookup-helper';
    expect(wrapper.find(inventoryErrorHelper).length).toBe(0);
    wrapper.find('input#name').simulate('change', {
      target: { value: mockFormValues.name, name: 'name' },
    });
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });
    wrapper.update();
    expect(wrapper.find(inventoryErrorHelper).length).toBe(1);
    expect(wrapper.find(inventoryErrorHelper).text()).toContain(
      'This field must not be blank'
    );
    expect(onSubmit).not.toHaveBeenCalled();
  });

  test('should show field error when form is saved without constructed plugin parameter', async () => {
    expect(wrapper.find('VariablesField .pf-m-error').length).toBe(0);
    await act(async () => {
      wrapper.find('VariablesField CodeEditor').invoke('onBlur')('');
    });
    wrapper.update();
    expect(wrapper.find('VariablesField .pf-m-error').length).toBe(1);
    expect(wrapper.find('VariablesField .pf-m-error').text()).toBe(
      'The plugin parameter is required.'
    );
  });

  test('should throw content error when option request fails', async () => {
    let newWrapper;
    ConstructedInventoriesAPI.readOptions.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      newWrapper = mountWithContexts(
        <ConstructedInventoryForm onCancel={() => {}} onSubmit={() => {}} />
      );
    });
    expect(newWrapper.find('ContentError').length).toBe(0);
    newWrapper.update();
    expect(newWrapper.find('ContentError').length).toBe(1);
    jest.clearAllMocks();
  });
});
