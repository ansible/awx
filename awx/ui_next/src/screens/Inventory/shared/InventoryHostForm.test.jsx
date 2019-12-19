import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';
import InventoryHostForm from './InventoryHostForm';

jest.mock('@api');

describe('<InventoryHostform />', () => {
  let wrapper;

  const handleSubmit = jest.fn();
  const handleCancel = jest.fn();

  const mockHostData = {
    name: 'foo',
    description: 'bar',
    inventory: 1,
    variables: '---\nfoo: bar',
  };

  beforeEach(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryHostForm
          handleCancel={handleCancel}
          handleSubmit={handleSubmit}
          host={mockHostData}
        />
      );
    });
  });

  afterEach(() => {
    wrapper.unmount();
  });

  test('should display form fields', () => {
    expect(wrapper.find('FormGroup[label="Name"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Description"]').length).toBe(1);
    expect(wrapper.find('VariablesField').length).toBe(1);
  });

  test('should call handleSubmit when Submit button is clicked', async () => {
    expect(handleSubmit).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Save"]').simulate('click');
    await sleep(1);
    expect(handleSubmit).toHaveBeenCalled();
  });

  test('should call handleCancel when Cancel button is clicked', async () => {
    expect(handleCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').simulate('click');
    await sleep(1);
    expect(handleCancel).toHaveBeenCalled();
  });
});
