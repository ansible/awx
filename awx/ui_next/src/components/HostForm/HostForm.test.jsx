import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import HostForm from './HostForm';

jest.mock('../../api');

const mockData = {
  id: 1,
  name: 'Foo',
  description: 'Bar',
  variables: '---',
  inventory: 1,
  summary_fields: {
    inventory: {
      id: 1,
      name: 'Test Inv',
    },
  },
};

describe('<HostForm />', () => {
  let wrapper;
  const handleSubmit = jest.fn();
  const handleCancel = jest.fn();

  beforeEach(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <HostForm
          host={mockData}
          handleSubmit={handleSubmit}
          handleCancel={handleCancel}
        />
      );
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('changing inputs should update form values', async () => {
    await act(async () => {
      wrapper.find('input#host-name').simulate('change', {
        target: { value: 'new foo', name: 'name' },
      });
      wrapper.find('input#host-description').simulate('change', {
        target: { value: 'new bar', name: 'description' },
      });
    });
    wrapper.update();
    expect(wrapper.find('input#host-name').prop('value')).toEqual('new foo');
    expect(wrapper.find('input#host-description').prop('value')).toEqual(
      'new bar'
    );
  });

  test('calls handleSubmit when form submitted', async () => {
    expect(handleSubmit).not.toHaveBeenCalled();
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });
    expect(handleSubmit).toHaveBeenCalledTimes(1);
  });

  test('calls "handleCancel" when Cancel button is clicked', () => {
    expect(handleCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(handleCancel).toHaveBeenCalledTimes(1);
  });

  test('should hide inventory lookup field', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <HostForm
          host={mockData}
          handleSubmit={jest.fn()}
          handleCancel={jest.fn()}
          isInventoryVisible={false}
        />
      );
    });
    expect(wrapper.find('InventoryLookupField').length).toBe(0);
  });
});
