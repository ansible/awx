import React from 'react';
import { act } from 'react-dom/test-utils';

import { CredentialTypesAPI, CredentialsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import CredentialTypeList from './CredentialTypeList';

jest.mock('../../../api/models/CredentialTypes');
jest.mock('../../../api/models/Credentials');

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

  beforeEach(() => {
    CredentialsAPI.read.mockResolvedValue({ data: { count: 0 } });
    CredentialTypesAPI.read.mockResolvedValue(credentialTypes);
    CredentialTypesAPI.readOptions.mockResolvedValue(options);
  });

  test('should mount successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<CredentialTypeList />);
    });
    await waitForElement(wrapper, 'CredentialTypeList', (el) => el.length > 0);
  });

  test('should have proper number of delete detail requests', () => {
    expect(
      wrapper.find('ToolbarDeleteButton').prop('deleteDetailsRequests')
    ).toHaveLength(1);
  });

  test('should have data fetched and render 2 rows', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<CredentialTypeList />);
    });
    await waitForElement(wrapper, 'CredentialTypeList', (el) => el.length > 0);
    expect(wrapper.find('CredentialTypeListItem').length).toBe(2);
    expect(CredentialTypesAPI.read).toBeCalled();
    expect(CredentialTypesAPI.readOptions).toBeCalled();
  });

  test('should delete item successfully', async () => {
    CredentialTypesAPI.read.mockResolvedValue(credentialTypes);
    await act(async () => {
      wrapper = mountWithContexts(<CredentialTypeList />);
    });
    await waitForElement(wrapper, 'CredentialTypeList', (el) => el.length > 0);

    wrapper
      .find('.pf-c-table__check')
      .first()
      .find('input')
      .simulate('change', credentialTypes.data.results[0]);
    wrapper.update();

    expect(
      wrapper.find('.pf-c-table__check').first().find('input').prop('checked')
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

  test('should not render add button', async () => {
    CredentialTypesAPI.readOptions.mockResolvedValue({
      data: { actions: { POST: false } },
    });
    await act(async () => {
      wrapper = mountWithContexts(<CredentialTypeList />);
    });
    waitForElement(wrapper, 'CredentialTypeList', (el) => el.length > 0);
    expect(wrapper.find('ToolbarAddButton').length).toBe(0);
  });

  test('should thrown content error', async () => {
    CredentialTypesAPI.destroy = jest.fn();
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
    await act(async () => {
      wrapper = mountWithContexts(<CredentialTypeList />);
    });
    await waitForElement(wrapper, 'CredentialTypeList', (el) => el.length > 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });

  test('should render deletion error modal', async () => {
    CredentialTypesAPI.destroy = jest.fn();
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
    await act(async () => {
      wrapper = mountWithContexts(<CredentialTypeList />);
    });
    waitForElement(wrapper, 'CredentialTypeList', (el) => el.length > 0);

    wrapper
      .find('.pf-c-table__check')
      .first()
      .find('input')
      .simulate('change', 'a');
    wrapper.update();
    expect(
      wrapper.find('.pf-c-table__check').first().find('input').prop('checked')
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
});
