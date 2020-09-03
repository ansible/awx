import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import UserTokenForm from './UserTokenForm';
import { sleep } from '../../../../testUtils/testUtils';
import { ApplicationsAPI } from '../../../api';

jest.mock('../../../api');
const applications = {
  data: {
    count: 2,
    results: [
      {
        id: 1,
        name: 'app',
        description: '',
      },
      {
        id: 4,
        name: 'application that should not crach',
        description: '',
      },
    ],
  },
};
describe('<UserTokenForm />', () => {
  let wrapper;
  beforeEach(() => {});
  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('initially renders successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserTokenForm handleSubmit={jest.fn()} handleCancel={jest.fn()} />
      );
    });

    expect(wrapper.find('UserTokenForm').length).toBe(1);
  });

  test('add form displays all form fields', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserTokenForm handleSubmit={jest.fn()} handleCancel={jest.fn()} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('FormGroup[name="application"]').length).toBe(1);
    expect(wrapper.find('FormField[name="description"]').length).toBe(1);
    expect(wrapper.find('FormGroup[name="scope"]').length).toBe(1);
  });

  test('inputs should update form value on change', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <UserTokenForm handleSubmit={jest.fn()} handleCancel={jest.fn()} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    wrapper.update();
    await act(async () => {
      wrapper.find('ApplicationLookup').invoke('onChange')({
        id: 1,
        name: 'application',
      });
      wrapper.find('input[name="description"]').simulate('change', {
        target: { value: 'new Bar', name: 'description' },
      });
      wrapper.find('AnsibleSelect[name="scope"]').prop('onChange')({}, 'read');
    });
    wrapper.update();
    expect(wrapper.find('ApplicationLookup').prop('value')).toEqual({
      id: 1,
      name: 'application',
    });
    expect(wrapper.find('input[name="description"]').prop('value')).toBe(
      'new Bar'
    );
    expect(wrapper.find('AnsibleSelect#token-scope').prop('value')).toBe(
      'read'
    );
  });

  test('should call handleSubmit when Submit button is clicked', async () => {
    ApplicationsAPI.read.mockResolvedValue(applications);
    const handleSubmit = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <UserTokenForm handleSubmit={handleSubmit} handleCancel={jest.fn()} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);

    await act(async () => {
      wrapper.find('AnsibleSelect[name="scope"]').prop('onChange')({}, 'read');
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').prop('onClick')();
    });
    await sleep(1);

    expect(handleSubmit).toBeCalled();
  });

  test('should call handleCancel when Cancel button is clicked', async () => {
    const handleCancel = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <UserTokenForm handleSubmit={jest.fn()} handleCancel={handleCancel} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(handleCancel).not.toHaveBeenCalled();
    wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    expect(handleCancel).toBeCalled();
  });
  test('should throw error on submit without scope value', async () => {
    ApplicationsAPI.read.mockResolvedValue(applications);
    const handleSubmit = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <UserTokenForm handleSubmit={handleSubmit} handleCancel={jest.fn()} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);

    await act(async () => {
      wrapper.find('button[aria-label="Save"]').prop('onClick')();
    });
    await sleep(1);
    wrapper.update();
    expect(
      wrapper.find('FormGroup[name="scope"]').prop('helperTextInvalid')
    ).toBe('Please enter a value.');
    expect(handleSubmit).not.toBeCalled();
  });
});
