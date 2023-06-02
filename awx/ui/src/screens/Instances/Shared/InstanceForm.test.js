import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import InstanceForm from './InstanceForm';

jest.mock('../../../api');

describe('<InstanceForm />', () => {
  let wrapper;
  let handleCancel;
  let handleSubmit;

  beforeAll(async () => {
    handleCancel = jest.fn();
    handleSubmit = jest.fn();

    await act(async () => {
      wrapper = mountWithContexts(
        <InstanceForm
          handleCancel={handleCancel}
          handleSubmit={handleSubmit}
          submitError={null}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  afterAll(() => {
    jest.clearAllMocks();
  });

  test('Initially renders successfully', () => {
    expect(wrapper.length).toBe(1);
  });

  test('should display form fields properly', async () => {
    await waitForElement(wrapper, 'InstanceForm', (el) => el.length > 0);
    expect(wrapper.find('FormGroup[label="Host Name"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Description"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Instance State"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Listener Port"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Instance Type"]').length).toBe(1);
  });

  test('should update form values', async () => {
    await act(async () => {
      wrapper.find('input#hostname').simulate('change', {
        target: { value: 'new Foo', name: 'hostname' },
      });
    });

    wrapper.update();
    expect(wrapper.find('input#hostname').prop('value')).toEqual('new Foo');
  });

  test('should call handleCancel when Cancel button is clicked', async () => {
    expect(handleCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    wrapper.update();
    expect(handleCancel).toBeCalled();
  });

  test('should call handleSubmit when Cancel button is clicked', async () => {
    expect(handleSubmit).not.toHaveBeenCalled();
    await act(async () => {
      wrapper.find('input#hostname').simulate('change', {
        target: { value: 'new Foo', name: 'hostname' },
      });
      wrapper.find('input#instance-description').simulate('change', {
        target: { value: 'This is a repeat song', name: 'description' },
      });
      wrapper.find('input#instance-port').simulate('change', {
        target: { value: 'This is a repeat song', name: 'listener_port' },
      });
    });
    wrapper.update();
    expect(
      wrapper.find('FormField[label="Instance State"]').prop('isDisabled')
    ).toBe(true);
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').invoke('onClick')();
    });

    expect(handleSubmit).toBeCalledWith({
      description: 'This is a repeat song',
      enabled: true,
      managed_by_policy: true,
      hostname: 'new Foo',
      listener_port: 'This is a repeat song',
      node_state: 'installed',
      node_type: 'execution',
    });
  });
});
