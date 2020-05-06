import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import CredentialChip from './CredentialChip';

describe('CredentialChip', () => {
  test('should render SSH kind', () => {
    const credential = {
      id: 1,
      kind: 'ssh',
      name: 'foo',
    };

    const wrapper = mountWithContexts(
      <CredentialChip credential={credential} />
    );
    expect(wrapper.find('CredentialChip').text()).toEqual('SSH: foo');
  });

  test('should render AWS kind', () => {
    const credential = {
      id: 1,
      kind: 'aws',
      name: 'foo',
    };

    const wrapper = mountWithContexts(
      <CredentialChip credential={credential} />
    );
    expect(wrapper.find('CredentialChip').text()).toEqual('AWS: foo');
  });

  test('should render with "Cloud"', () => {
    const credential = {
      id: 1,
      cloud: true,
      kind: 'other',
      name: 'foo',
    };

    const wrapper = mountWithContexts(
      <CredentialChip credential={credential} />
    );
    expect(wrapper.find('CredentialChip').text()).toEqual('Cloud: foo');
  });

  test('should render with other kind', () => {
    const credential = {
      id: 1,
      kind: 'other',
      name: 'foo',
    };

    const wrapper = mountWithContexts(
      <CredentialChip credential={credential} />
    );
    expect(wrapper.find('CredentialChip').text()).toEqual('Other: foo');
  });
});
