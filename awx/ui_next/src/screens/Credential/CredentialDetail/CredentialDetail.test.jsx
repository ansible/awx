import React from 'react';
import { act } from 'react-dom/test-utils';
import { CredentialsAPI, CredentialTypesAPI } from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import CredentialDetail from './CredentialDetail';
import { mockCredentials, mockCredentialType } from '../shared';

jest.mock('@api');

const mockCredential = mockCredentials.results[0];

CredentialTypesAPI.readDetail.mockResolvedValue({
  data: mockCredentialType,
});

function expectDetailToMatch(wrapper, label, value) {
  const detail = wrapper.find(`Detail[label="${label}"]`);
  expect(detail).toHaveLength(1);
  expect(detail.find('dd').text()).toEqual(value);
}

describe('<CredentialDetail />', () => {
  let wrapper;

  beforeEach(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <CredentialDetail credential={mockCredential} />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  test('should render successfully', () => {
    expect(wrapper.find('CredentialDetail').length).toBe(1);
  });

  test('should render details', () => {
    expectDetailToMatch(wrapper, 'Name', mockCredential.name);
    expectDetailToMatch(wrapper, 'Description', mockCredential.description);
    expectDetailToMatch(
      wrapper,
      'Organization',
      mockCredential.summary_fields.organization.name
    );
    expectDetailToMatch(
      wrapper,
      'Credential Type',
      mockCredential.summary_fields.credential_type.name
    );
    expectDetailToMatch(wrapper, 'Username', mockCredential.inputs.username);
    expectDetailToMatch(
      wrapper,
      'Privilege Escalation Method',
      mockCredential.inputs.become_method
    );
    expectDetailToMatch(
      wrapper,
      'Privilege Escalation Username',
      mockCredential.inputs.become_username
    );
    expect(wrapper.find(`Detail[label="Options"] ListItem`).text()).toEqual(
      'Authorize'
    );
  });

  test('should show content error on throw', async () => {
    CredentialTypesAPI.readDetail.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <CredentialDetail credential={mockCredential} />
      );
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });

  test('handleDelete should call api', async () => {
    CredentialsAPI.destroy = jest.fn();
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    wrapper.update();
    expect(CredentialsAPI.destroy).toHaveBeenCalledTimes(1);
  });

  test('should show error modal when credential is not successfully deleted from api', async () => {
    CredentialsAPI.destroy.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    await waitForElement(wrapper, 'ErrorDetail', el => el.length === 1);
    await act(async () => {
      wrapper.find('ModalBoxCloseButton').invoke('onClose')();
    });
  });
});
