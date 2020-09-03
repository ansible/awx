import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { CredentialTypesAPI } from '../../../api';
import CredentialTypeAdd from './CredentialTypeAdd';

jest.mock('../../../api');

const credentialTypeData = {
  name: 'Foo',
  description: 'Bar',
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
};

CredentialTypesAPI.create.mockResolvedValue({
  data: {
    id: 42,
  },
});

describe('<CredentialTypeAdd/>', () => {
  let wrapper;
  let history;

  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/credential_types'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<CredentialTypeAdd />, {
        context: { router: { history } },
      });
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('handleSubmit should call the api and redirect to details page', async () => {
    await act(async () => {
      wrapper.find('CredentialTypeForm').prop('onSubmit')(credentialTypeData);
    });
    wrapper.update();
    expect(CredentialTypesAPI.create).toHaveBeenCalledWith({
      ...credentialTypeData,
      inputs: JSON.parse(credentialTypeData.inputs),
      injectors: JSON.parse(credentialTypeData.injectors),
    });
    expect(history.location.pathname).toBe('/credential_types/42/details');
  });

  test('handleCancel should return the user back to the credential types list', async () => {
    wrapper.find('Button[aria-label="Cancel"]').simulate('click');
    expect(history.location.pathname).toEqual('/credential_types');
  });

  test('failed form submission should show an error message', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    CredentialTypesAPI.create.mockImplementationOnce(() =>
      Promise.reject(error)
    );
    await act(async () => {
      wrapper.find('CredentialTypeForm').invoke('onSubmit')(credentialTypeData);
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
  });
});
