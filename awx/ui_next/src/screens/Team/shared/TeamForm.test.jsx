import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';

import TeamForm from './TeamForm';

jest.mock('@api');

describe('<TeamForm />', () => {
  let wrapper;
  const meConfig = {
    me: {
      is_superuser: false,
    },
  };
  const mockData = {
    id: 1,
    name: 'Foo',
    description: 'Bar',
    organization: 1,
    summary_fields: {
      id: 1,
      name: 'Default',
    },
  };

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('changing inputs should update form values', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <TeamForm
          team={mockData}
          handleSubmit={jest.fn()}
          handleCancel={jest.fn()}
          me={meConfig.me}
        />
      );
    });

    const form = wrapper.find('Formik');
    wrapper.find('input#team-name').simulate('change', {
      target: { value: 'new foo', name: 'name' },
    });
    expect(form.state('values').name).toEqual('new foo');
    wrapper.find('input#team-description').simulate('change', {
      target: { value: 'new bar', name: 'description' },
    });
    expect(form.state('values').description).toEqual('new bar');
    act(() => {
      wrapper.find('OrganizationLookup').invoke('onBlur')();
      wrapper.find('OrganizationLookup').invoke('onChange')({
        id: 2,
        name: 'Other Org',
      });
    });
    expect(form.state('values').organization).toEqual(2);
  });

  test('should call handleSubmit when Submit button is clicked', async () => {
    const handleSubmit = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <TeamForm
          team={mockData}
          handleSubmit={handleSubmit}
          handleCancel={jest.fn()}
          me={meConfig.me}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(handleSubmit).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Save"]').simulate('click');
    await sleep(1);
    expect(handleSubmit).toBeCalled();
  });

  test('calls handleCancel when Cancel button is clicked', async () => {
    const handleCancel = jest.fn();

    await act(async () => {
      wrapper = mountWithContexts(
        <TeamForm
          team={mockData}
          handleSubmit={jest.fn()}
          handleCancel={handleCancel}
          me={meConfig.me}
        />
      );
    });
    expect(handleCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(handleCancel).toBeCalled();
  });
});
