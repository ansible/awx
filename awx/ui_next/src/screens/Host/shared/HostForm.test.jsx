import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '@testUtils/enzymeHelpers';

import HostForm from './HostForm';

jest.mock('@api');

describe('<HostForm />', () => {
  const meConfig = {
    me: {
      is_superuser: false,
    },
  };
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

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('changing inputs should update form values', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <HostForm
          host={mockData}
          handleSubmit={jest.fn()}
          handleCancel={jest.fn()}
          me={meConfig.me}
        />
      );
    });

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
    const handleSubmit = jest.fn();
    const wrapper = mountWithContexts(
      <HostForm
        host={mockData}
        handleSubmit={handleSubmit}
        handleCancel={jest.fn()}
        me={meConfig.me}
      />
    );
    expect(handleSubmit).not.toHaveBeenCalled();
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });
    expect(handleSubmit).toHaveBeenCalled();
  });

  test('calls "handleCancel" when Cancel button is clicked', () => {
    const handleCancel = jest.fn();

    const wrapper = mountWithContexts(
      <HostForm
        host={mockData}
        handleSubmit={jest.fn()}
        handleCancel={handleCancel}
        me={meConfig.me}
      />
    );
    expect(handleCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(handleCancel).toBeCalled();
  });
});
