import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import selectedCredential from '../data.cyberArkCredential.json';
import CredentialPluginSelected from './CredentialPluginSelected';

describe('<CredentialPluginSelected />', () => {
  let wrapper;
  const onClearPlugin = jest.fn();
  const onEditPlugin = jest.fn();
  beforeAll(() => {
    wrapper = mountWithContexts(
      <CredentialPluginSelected
        credential={selectedCredential}
        onClearPlugin={onClearPlugin}
        onEditPlugin={onEditPlugin}
      />
    );
  });
  afterAll(() => {
    wrapper.unmount();
  });
  test('renders the expected content', () => {
    expect(wrapper.find('CredentialChip').length).toBe(1);
    expect(wrapper.find('KeyIcon').length).toBe(1);
  });
  test('clearing plugin calls expected function', () => {
    wrapper.find('CredentialChip button').simulate('click');
    expect(onClearPlugin).toBeCalledTimes(1);
  });
  test('editing plugin calls expected function', () => {
    wrapper.find('KeyIcon').simulate('click');
    expect(onEditPlugin).toBeCalledTimes(1);
  });
});
