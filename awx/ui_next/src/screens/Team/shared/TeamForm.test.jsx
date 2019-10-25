import React from 'react';

import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';

import TeamForm from './TeamForm';

jest.mock('@api');

describe('<TeamForm />', () => {
  const meConfig = {
    me: {
      is_superuser: false,
    },
  };
  const mockData = {
    id: 1,
    name: 'Foo',
    description: 'Bar',
  };

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('changing inputs should update form values', () => {
    const wrapper = mountWithContexts(
      <TeamForm
        team={mockData}
        handleSubmit={jest.fn()}
        handleCancel={jest.fn()}
        me={meConfig.me}
      />
    );

    const form = wrapper.find('Formik');
    wrapper.find('input#team-name').simulate('change', {
      target: { value: 'new foo', name: 'name' },
    });
    expect(form.state('values').name).toEqual('new foo');
    wrapper.find('input#team-description').simulate('change', {
      target: { value: 'new bar', name: 'description' },
    });
    expect(form.state('values').description).toEqual('new bar');
  });

  test('calls handleSubmit when form submitted', async () => {
    const handleSubmit = jest.fn();
    const wrapper = mountWithContexts(
      <TeamForm
        team={mockData}
        handleSubmit={handleSubmit}
        handleCancel={jest.fn()}
        me={meConfig.me}
      />
    );
    expect(handleSubmit).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Save"]').simulate('click');
    await sleep(1);
    expect(handleSubmit).toHaveBeenCalledWith({
      name: 'Foo',
      description: 'Bar',
    });
  });

  test('calls "handleCancel" when Cancel button is clicked', () => {
    const handleCancel = jest.fn();

    const wrapper = mountWithContexts(
      <TeamForm
        team={mockData}
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
