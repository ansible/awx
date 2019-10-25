import React from 'react';

import { mountWithContexts } from '@testUtils/enzymeHelpers';
import MultiCredentialsLookup from './MultiCredentialsLookup';
import { CredentialsAPI, CredentialTypesAPI } from '@api';

jest.mock('@api');

describe('<MultiCredentialsLookup />', () => {
  let wrapper;
  let lookup;
  let credLookup;
  let onChange;

  const credentials = [
    { id: 1, kind: 'cloud', name: 'Foo', url: 'www.google.com' },
    { id: 2, kind: 'ssh', name: 'Alex', url: 'www.google.com' },
    { name: 'Gatsby', id: 21, kind: 'vault' },
    { name: 'Gatsby', id: 8, kind: 'Machine' },
  ];
  beforeEach(() => {
    CredentialTypesAPI.read.mockResolvedValue({
      data: {
        results: [
          {
            id: 400,
            kind: 'ssh',
            namespace: 'biz',
            name: 'Amazon Web Services',
          },
          { id: 500, kind: 'vault', namespace: 'buzz', name: 'Vault' },
          { id: 600, kind: 'machine', namespace: 'fuzz', name: 'Machine' },
        ],
        count: 2,
      },
    });
    CredentialsAPI.read.mockResolvedValueOnce({
      data: {
        results: [
          { id: 1, kind: 'cloud', name: 'Cred 1', url: 'www.google.com' },
          { id: 2, kind: 'ssh', name: 'Cred 2', url: 'www.google.com' },
          { id: 3, kind: 'Ansible', name: 'Cred 3', url: 'www.google.com' },
          { id: 4, kind: 'Machine', name: 'Cred 4', url: 'www.google.com' },
          { id: 5, kind: 'Machine', name: 'Cred 5', url: 'www.google.com' },
        ],
        count: 3,
      },
    });
    onChange = jest.fn();
    wrapper = mountWithContexts(
      <MultiCredentialsLookup
        onError={() => {}}
        credentials={credentials}
        onChange={onChange}
        tooltip="This is credentials look up"
      />
    );
    lookup = wrapper.find('Lookup');
    credLookup = wrapper.find('MultiCredentialsLookup');
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('MultiCredentialsLookup renders properly', () => {
    expect(wrapper.find('MultiCredentialsLookup')).toHaveLength(1);
    expect(CredentialTypesAPI.read).toHaveBeenCalled();
  });

  test('onChange is called when you click to remove a credential from input', async () => {
    const chip = wrapper.find('PFChip');
    const button = chip.at(1).find('Button');
    expect(chip).toHaveLength(4);
    button.prop('onClick')();
    expect(onChange).toBeCalledWith([
      { id: 1, kind: 'cloud', name: 'Foo', url: 'www.google.com' },
      { id: 21, kind: 'vault', name: 'Gatsby' },
      { id: 8, kind: 'Machine', name: 'Gatsby' },
    ]);
  });

  test('can change credential types', () => {
    lookup.prop('selectCategory')({}, 'Vault');
    expect(credLookup.state('selectedCredentialType')).toEqual({
      id: 500,
      key: 500,
      kind: 'vault',
      type: 'buzz',
      value: 'Vault',
      label: 'Vault',
      isDisabled: false,
    });
    expect(CredentialsAPI.read).toHaveBeenCalled();
  });
  test('Toggle credentials only adds 1 credential per credential type except vault(see below)', () => {
    lookup.prop('onToggleItem')({ name: 'Party', id: 9, kind: 'Machine' });
    expect(onChange).toBeCalledWith([
      { id: 1, kind: 'cloud', name: 'Foo', url: 'www.google.com' },
      { id: 2, kind: 'ssh', name: 'Alex', url: 'www.google.com' },
      { id: 21, kind: 'vault', name: 'Gatsby' },
      { id: 9, kind: 'Machine', name: 'Party' },
    ]);
  });
  test('Toggle credentials only adds 1 credential per credential type', () => {
    lookup.prop('onToggleItem')({ name: 'Party', id: 22, kind: 'vault' });
    expect(onChange).toBeCalledWith([
      ...credentials,
      { name: 'Party', id: 22, kind: 'vault' },
    ]);
  });
});
