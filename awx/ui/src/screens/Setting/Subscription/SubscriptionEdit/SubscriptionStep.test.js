import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import SubscriptionStep from './SubscriptionStep';

describe('<SubscriptionStep />', () => {
  let wrapper;

  beforeAll(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik
          initialValues={{
            insights: false,
            manifest_file: null,
            manifest_filename: '',
            pendo: false,
            subscription: null,
            password: '',
            username: '',
          }}
        >
          <SubscriptionStep />
        </Formik>
      );
    });
  });

  afterAll(() => {
    jest.clearAllMocks();
  });

  test('initially renders without crashing', async () => {
    expect(wrapper.find('SubscriptionStep').length).toBe(1);
  });

  test('should update filename when a manifest zip file is uploaded', async () => {
    expect(wrapper.find('FileUploadField')).toHaveLength(1);
    expect(wrapper.find('label').text()).toEqual(
      'Red Hat subscription manifest'
    );
    expect(wrapper.find('FileUploadField').prop('value')).toEqual(null);
    expect(wrapper.find('FileUploadField').prop('filename')).toEqual('');
    const mockFile = new Blob(['123'], { type: 'application/zip' });
    mockFile.name = 'new file name';
    mockFile.date = new Date();
    await act(async () => {
      wrapper.find('FileUpload').invoke('onChange')(mockFile, 'new file name');
    });
    await act(async () => {
      wrapper.update();
    });
    await act(async () => {
      wrapper.update();
    });
    expect(wrapper.find('FileUploadField').prop('value')).toEqual(
      expect.stringMatching(/^[\x00-\x7F]+$/) // eslint-disable-line no-control-regex
    );
    expect(wrapper.find('FileUploadField').prop('filename')).toEqual(
      'new file name'
    );
  });

  test('clear button should clear manifest value and filename', async () => {
    await act(async () => {
      wrapper
        .find('FileUpload .pf-c-input-group button')
        .last()
        .simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('FileUploadField').prop('value')).toEqual(null);
    expect(wrapper.find('FileUploadField').prop('filename')).toEqual('');
  });

  test('FileUpload should throw an error', async () => {
    expect(
      wrapper.find('div#subscription-manifest-helper.pf-m-error')
    ).toHaveLength(0);
    await act(async () => {
      wrapper.find('FileUpload').invoke('onChange')('✓', 'new file name');
    });
    wrapper.update();
    expect(
      wrapper.find('div#subscription-manifest-helper.pf-m-error')
    ).toHaveLength(1);
    expect(wrapper.find('div#subscription-manifest-helper').text()).toContain(
      'Invalid file format. Please upload a valid Red Hat Subscription Manifest.'
    );
  });

  test('Username/password toggle button should show username credential fields', async () => {
    expect(wrapper.find('ToggleGroupItem').last().props().isSelected).toBe(
      false
    );
    wrapper
      .find('ToggleGroupItem[text="Username / password"] button')
      .simulate('click');
    wrapper.update();
    expect(wrapper.find('ToggleGroupItem').last().props().isSelected).toBe(
      true
    );
    await act(async () => {
      wrapper.find('input#username-field').simulate('change', {
        target: { value: 'username-cred', name: 'username' },
      });
      wrapper.find('input#password-field').simulate('change', {
        target: { value: 'password-cred', name: 'password' },
      });
    });
    wrapper.update();
    expect(wrapper.find('input#username-field').prop('value')).toEqual(
      'username-cred'
    );
    expect(wrapper.find('input#password-field').prop('value')).toEqual(
      'password-cred'
    );
  });
});
