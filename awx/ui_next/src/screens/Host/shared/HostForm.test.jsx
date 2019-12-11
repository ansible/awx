import React from 'react';

import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';

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

  test('changing inputs should update form values', () => {
    const wrapper = mountWithContexts(
      <HostForm
        host={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
        me={meConfig.me}
      />
    );

    const form = wrapper.find('Formik');
    wrapper.find('input#host-name').simulate('change', {
      target: { value: 'new foo', name: 'name' },
    });
    expect(form.state('values').name).toEqual('new foo');
    wrapper.find('input#host-description').simulate('change', {
      target: { value: 'new bar', name: 'description' },
    });
    expect(form.state('values').description).toEqual('new bar');
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
    wrapper.find('button[aria-label="Save"]').simulate('click');
    await sleep(1);
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
