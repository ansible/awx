import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import TeamForm from './TeamForm';

jest.mock('../../../api');

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

    act(() => {
      wrapper.find('input#team-name').simulate('change', {
        target: { value: 'new foo', name: 'name' },
      });
      wrapper.find('input#team-description').simulate('change', {
        target: { value: 'new bar', name: 'description' },
      });
      wrapper.find('OrganizationLookup').invoke('onBlur')();
      wrapper.find('OrganizationLookup').invoke('onChange')({
        id: 2,
        name: 'Other Org',
      });
    });
    wrapper.update();
    expect(wrapper.find('input#team-name').prop('value')).toEqual('new foo');
    expect(wrapper.find('input#team-description').prop('value')).toEqual(
      'new bar'
    );
    expect(wrapper.find('OrganizationLookup').prop('value')).toEqual({
      id: 2,
      name: 'Other Org',
    });
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
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });
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
