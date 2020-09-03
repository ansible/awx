import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { CredentialTypesAPI } from '../../../api';

import CredentialTypeEdit from './CredentialTypeEdit';

jest.mock('../../../api');

const credentialTypeData = {
  id: 42,
  name: 'Foo',
  description: 'New credential',
  kind: 'cloud',
  inputs: JSON.stringify({
    fields: [
      {
        id: 'username',
        type: 'string',
        label: 'Jenkins username',
      },
      {
        id: 'password',
        type: 'string',
        label: 'Jenkins password',
        secret: true,
      },
    ],
    required: ['username', 'password'],
  }),
  injectors: JSON.stringify({
    extra_vars: {
      Jenkins_password: '{{ password }}',
      Jenkins_username: '{{ username }}',
    },
  }),
  summary_fields: {
    created_by: {
      id: 1,
      username: 'admin',
      first_name: '',
      last_name: '',
    },
    modified_by: {
      id: 1,
      username: 'admin',
      first_name: '',
      last_name: '',
    },
    user_capabilities: {
      edit: true,
      delete: true,
    },
  },
  created: '2020-06-25T16:52:36.127008Z',
  modified: '2020-06-25T16:52:36.127022Z',
};

const updateCredentialTypeData = {
  name: 'Bar',
  description: 'Updated new Credential Type',
  injectors: credentialTypeData.injectors,
  inputs: credentialTypeData.inputs,
};

describe('<CredentialTypeEdit>', () => {
  let wrapper;
  let history;

  beforeAll(async () => {
    history = createMemoryHistory();
    await act(async () => {
      wrapper = mountWithContexts(
        <CredentialTypeEdit credentialType={credentialTypeData} />,
        {
          context: { router: { history } },
        }
      );
    });
  });

  afterAll(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('handleSubmit should call the api and redirect to details page', async () => {
    await act(async () => {
      wrapper.find('CredentialTypeForm').invoke('onSubmit')(
        updateCredentialTypeData
      );
      wrapper.update();
      expect(CredentialTypesAPI.update).toHaveBeenCalledWith(42, {
        ...updateCredentialTypeData,
        injectors: JSON.parse(credentialTypeData.injectors),
        inputs: JSON.parse(credentialTypeData.inputs),
      });
    });
  });

  test('should navigate to credential types detail when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    });
    expect(history.location.pathname).toEqual('/credential_types/42/details');
  });

  test('should navigate to credential type detail after successful submission', async () => {
    await act(async () => {
      wrapper.find('CredentialTypeForm').invoke('onSubmit')({
        ...updateCredentialTypeData,
        injectors: JSON.parse(credentialTypeData.injectors),
        inputs: JSON.parse(credentialTypeData.inputs),
      });
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(0);
    expect(history.location.pathname).toEqual('/credential_types/42/details');
  });

  test('failed form submission should show an error message', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    CredentialTypesAPI.update.mockImplementationOnce(() =>
      Promise.reject(error)
    );
    await act(async () => {
      wrapper.find('CredentialTypeForm').invoke('onSubmit')(
        updateCredentialTypeData
      );
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
  });
});
