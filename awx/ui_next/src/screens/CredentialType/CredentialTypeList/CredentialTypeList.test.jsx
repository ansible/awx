import React from 'react';
import { act } from 'react-dom/test-utils';

import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import { CredentialTypesAPI } from '../../../api';
import CredentialTypeList from './CredentialTypeList';

jest.mock('../../../api/models/CredentialTypes');

const credentialTypes = {
  data: {
    results: [
      {
        id: 1,
        name: 'Foo',
        kind: 'cloud',
        summary_fields: {
          user_capabilities: { edit: true, delete: true },
        },
        url: '',
      },
      {
        id: 2,
        name: 'Bar',
        kind: 'cloud',
        summary_fields: {
          user_capabilities: { edit: false, delete: true },
        },
        url: '',
      },
    ],
    count: 2,
  },
};

const options = { data: { actions: { POST: true } } };

describe('<CredentialTypeList', () => {
  let wrapper;

  test('should mount successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<CredentialTypeList />);
    });
    await waitForElement(wrapper, 'CredentialTypeList', el => el.length > 0);
  });

  test('should have data fetched and render 2 rows', async () => {
    CredentialTypesAPI.read.mockResolvedValue(credentialTypes);
    CredentialTypesAPI.readOptions.mockResolvedValue(options);

    await act(async () => {
      wrapper = mountWithContexts(<CredentialTypeList />);
    });
    await waitForElement(wrapper, 'CredentialTypeList', el => el.length > 0);
    expect(wrapper.find('CredentialTypeListItem').length).toBe(2);
    expect(CredentialTypesAPI.read).toBeCalled();
    expect(CredentialTypesAPI.readOptions).toBeCalled();
  });

  test('should delete item successfully', async () => {
    CredentialTypesAPI.read.mockResolvedValue(credentialTypes);
    CredentialTypesAPI.readOptions.mockResolvedValue(options);

    await act(async () => {
      wrapper = mountWithContexts(<CredentialTypeList />);
    });
    await waitForElement(wrapper, 'CredentialTypeList', el => el.length > 0);

    wrapper
      .find('input#select-credential-types-1')
      .simulate('change', credentialTypes.data.results[0]);
    wrapper.update();

    expect(
      wrapper.find('input#select-credential-types-1').prop('checked')
    ).toBe(true);

    await act(async () => {
      wrapper.find('Button[aria-label="Delete"]').prop('onClick')();
    });
    wrapper.update();

    await act(async () =>
      wrapper.find('Button[aria-label="confirm delete"]').prop('onClick')()
    );

    expect(CredentialTypesAPI.destroy).toBeCalledWith(
      credentialTypes.data.results[0].id
    );
  });

  test('should thrown content error', async () => {
    CredentialTypesAPI.read.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'GET',
            url: '/api/v2/credential_types',
          },
          data: 'An error occurred',
        },
      })
    );
    CredentialTypesAPI.readOptions.mockResolvedValue(options);
    await act(async () => {
      wrapper = mountWithContexts(<CredentialTypeList />);
    });
    await waitForElement(wrapper, 'CredentialTypeList', el => el.length > 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });

  test('should render deletion error modal', async () => {
    CredentialTypesAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'DELETE',
            url: '/api/v2/credential_types',
          },
          data: 'An error occurred',
        },
      })
    );
    CredentialTypesAPI.read.mockResolvedValue(credentialTypes);
    CredentialTypesAPI.readOptions.mockResolvedValue(options);
    await act(async () => {
      wrapper = mountWithContexts(<CredentialTypeList />);
    });
    waitForElement(wrapper, 'CredentialTypeList', el => el.length > 0);

    wrapper.find('input#select-credential-types-1').simulate('change', 'a');
    wrapper.update();
    expect(
      wrapper.find('input#select-credential-types-1').prop('checked')
    ).toBe(true);

    await act(async () =>
      wrapper.find('Button[aria-label="Delete"]').prop('onClick')()
    );
    wrapper.update();

    await act(async () =>
      wrapper.find('Button[aria-label="confirm delete"]').prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find('ErrorDetail').length).toBe(1);
  });

  test('should not render add button', async () => {
    CredentialTypesAPI.read.mockResolvedValue(credentialTypes);
    CredentialTypesAPI.readOptions.mockResolvedValue({
      data: { actions: { POST: false } },
    });
    await act(async () => {
      wrapper = mountWithContexts(<CredentialTypeList />);
    });
    waitForElement(wrapper, 'CredentialTypeList', el => el.length > 0);
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
  });
});
