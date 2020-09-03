import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { CredentialTypesAPI } from '../../../api';
import { jsonToYaml } from '../../../util/yaml';

import CredentialTypeDetails from './CredentialTypeDetails';

jest.mock('../../../api');

const credentialTypeData = {
  name: 'Foo',
  description: 'Bar',
  kind: 'cloud',
  inputs: {
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
  },
  injectors: {
    extra_vars: {
      Jenkins_password: '{{ password }}',
      Jenkins_username: '{{ username }}',
    },
  },
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

function expectDetailToMatch(wrapper, label, value) {
  const detail = wrapper.find(`Detail[label="${label}"]`);
  expect(detail).toHaveLength(1);
  expect(detail.prop('value')).toEqual(value);
}

describe('<CredentialTypeDetails/>', () => {
  let wrapper;
  test('should render details properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <CredentialTypeDetails credentialType={credentialTypeData} />
      );
    });
    wrapper.update();
    expectDetailToMatch(wrapper, 'Name', credentialTypeData.name);
    expectDetailToMatch(wrapper, 'Description', credentialTypeData.description);
    const dates = wrapper.find('UserDateDetail');
    expect(dates).toHaveLength(2);
    expect(dates.at(0).prop('date')).toEqual(credentialTypeData.created);
    expect(dates.at(1).prop('date')).toEqual(credentialTypeData.modified);
    const vars = wrapper.find('VariablesDetail');
    expect(vars).toHaveLength(2);

    expect(vars.at(0).prop('label')).toEqual('Input configuration');
    expect(vars.at(0).prop('value')).toEqual(
      jsonToYaml(JSON.stringify(credentialTypeData.inputs))
    );
    expect(vars.at(1).prop('label')).toEqual('Injector configuration');
    expect(vars.at(1).prop('value')).toEqual(
      jsonToYaml(JSON.stringify(credentialTypeData.injectors))
    );
  });

  test('expected api call is made for delete', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/credential_types/42/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <CredentialTypeDetails credentialType={credentialTypeData} />,
        {
          context: { router: { history } },
        }
      );
    });
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    expect(CredentialTypesAPI.destroy).toHaveBeenCalledTimes(1);
    expect(history.location.pathname).toBe('/credential_types');
  });

  test('should not render delete button', async () => {
    credentialTypeData.summary_fields.user_capabilities.delete = false;
    await act(async () => {
      wrapper = mountWithContexts(
        <CredentialTypeDetails credentialType={credentialTypeData} />
      );
    });
    wrapper.update();

    expect(wrapper.find('Button[aria-label="Delete"]').length).toBe(0);
  });
  test('should not render edit button', async () => {
    credentialTypeData.summary_fields.user_capabilities.edit = false;
    await act(async () => {
      wrapper = mountWithContexts(
        <CredentialTypeDetails credentialType={credentialTypeData} />
      );
    });
    wrapper.update();

    expect(wrapper.find('Button[aria-label="Edit"]').length).toBe(0);
  });
});
