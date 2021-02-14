import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import MultiCredentialsLookup from './MultiCredentialsLookup';
import { CredentialsAPI, CredentialTypesAPI } from '../../api';

jest.mock('../../api');

describe('<MultiCredentialsLookup />', () => {
  let wrapper;

  const credentials = [
    {
      id: 1,
      credential_type: 1,
      kind: 'gce',
      name: 'Foo',
      url: 'www.google.com',
    },
    {
      id: 2,
      credential_type: 2,
      kind: 'ssh',
      name: 'Alex',
      url: 'www.google.com',
    },
    {
      id: 21,
      credential_type: 3,
      kind: 'vault',
      inputs: { vault_id: '1' },
      name: 'Gatsby',
    },
    { id: 23, credential_type: 3, kind: 'vault', name: 'Gatsby 2' },
    { id: 8, credential_type: 4, kind: 'Machine', name: 'Gatsby' },
  ];

  beforeEach(() => {
    CredentialTypesAPI.loadAllTypes.mockResolvedValueOnce([
      {
        id: 400,
        kind: 'ssh',
        namespace: 'biz',
        name: 'Amazon Web Services',
      },
      { id: 500, kind: 'vault', namespace: 'buzz', name: 'Vault' },
      { id: 600, kind: 'machine', namespace: 'fuzz', name: 'Machine' },
    ]);
    CredentialsAPI.read.mockResolvedValueOnce({
      data: {
        results: [
          {
            id: 1,
            credential_type: 1,
            kind: 'gc2',
            name: 'Cred 1',
            url: 'www.google.com',
          },
          {
            id: 2,
            credential_type: 2,
            kind: 'ssh',
            name: 'Cred 2',
            url: 'www.google.com',
          },
          {
            id: 3,
            credential_type: 5,
            kind: 'Ansible',
            name: 'Cred 3',
            url: 'www.google.com',
          },
          {
            id: 4,
            credential_type: 4,
            kind: 'Machine',
            name: 'Cred 4',
            url: 'www.google.com',
          },
          {
            id: 5,
            credential_type: 4,
            kind: 'Machine',
            name: 'Cred 5',
            url: 'www.google.com',
          },

          {
            id: 6,
            credential_type: 5,
            kind: 'vault',
            name: 'Cred 6',
            url: 'www.google.com',
            inputs: { vault_id: 'vault ID' },
          },
          {
            id: 7,
            credential_type: 5,
            kind: 'vault',
            name: 'Cred 7',
            url: 'www.google.com',
            inputs: {},
          },
        ],
        count: 3,
      },
    });
    CredentialsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('should load credential types', async () => {
    const onChange = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <MultiCredentialsLookup
          value={credentials}
          tooltip="This is credentials look up"
          onChange={onChange}
          onError={() => {}}
        />
      );
    });
    wrapper.update();
    expect(wrapper.find('MultiCredentialsLookup')).toHaveLength(1);
    expect(CredentialTypesAPI.loadAllTypes).toHaveBeenCalled();
  });

  test('onChange is called when you click to remove a credential from input', async () => {
    const onChange = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <MultiCredentialsLookup
          value={credentials}
          tooltip="This is credentials look up"
          onChange={onChange}
          onError={() => {}}
        />
      );
    });
    const chip = wrapper.find('CredentialChip');
    expect(chip).toHaveLength(5);
    const button = chip.at(1).find('Chip Button');
    await act(async () => {
      button.invoke('onClick')();
    });
    expect(onChange).toBeCalledWith([
      {
        id: 1,
        credential_type: 1,
        kind: 'gce',
        name: 'Foo',
        url: 'www.google.com',
      },
      {
        id: 21,
        credential_type: 3,
        kind: 'vault',
        inputs: { vault_id: '1' },
        name: 'Gatsby',
      },
      { id: 23, credential_type: 3, kind: 'vault', name: 'Gatsby 2' },
      { id: 8, credential_type: 4, kind: 'Machine', name: 'Gatsby' },
    ]);
  });

  test('should change credential types', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <MultiCredentialsLookup
          value={credentials}
          tooltip="This is credentials look up"
          onChange={() => {}}
          onError={() => {}}
        />
      );
    });
    const searchButton = await waitForElement(
      wrapper,
      'Button[aria-label="Search"]'
    );
    await act(async () => {
      searchButton.invoke('onClick')();
    });
    const select = await waitForElement(wrapper, 'AnsibleSelect');
    CredentialsAPI.read.mockResolvedValueOnce({
      data: {
        results: [
          { id: 1, kind: 'cloud', name: 'New Cred', url: 'www.google.com' },
        ],
        count: 1,
      },
    });
    expect(CredentialsAPI.read).toHaveBeenCalledTimes(1);
    await act(async () => {
      select.invoke('onChange')({}, 500);
    });
    wrapper.update();
    expect(CredentialsAPI.read).toHaveBeenCalledTimes(2);
    expect(wrapper.find('OptionsList').prop('options')).toEqual([
      {
        id: 1,
        kind: 'cloud',
        name: 'New Cred',
        url: 'www.google.com',
        label: 'New Cred',
      },
    ]);
  });

  test('should only add 1 credential per credential type except vault(see below)', async () => {
    const onChange = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <MultiCredentialsLookup
          value={credentials}
          tooltip="This is credentials look up"
          onChange={onChange}
          onError={() => {}}
        />
      );
    });
    const searchButton = await waitForElement(
      wrapper,
      'Button[aria-label="Search"]'
    );
    await act(async () => {
      searchButton.invoke('onClick')();
    });
    wrapper.update();
    const optionsList = wrapper.find('OptionsList');
    expect(optionsList.prop('multiple')).toEqual(false);
    act(() => {
      optionsList.invoke('selectItem')({
        id: 5,
        credential_type: 4,
        kind: 'Machine',
        name: 'Cred 5',
        url: 'www.google.com',
      });
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('Button[variant="primary"]').invoke('onClick')();
    });
    expect(onChange).toBeCalledWith([
      {
        id: 1,
        credential_type: 1,
        kind: 'gce',
        name: 'Foo',
        url: 'www.google.com',
      },
      {
        id: 2,
        credential_type: 2,
        kind: 'ssh',
        name: 'Alex',
        url: 'www.google.com',
      },
      {
        id: 21,
        credential_type: 3,
        kind: 'vault',
        inputs: { vault_id: '1' },
        name: 'Gatsby',
      },
      { id: 23, credential_type: 3, kind: 'vault', name: 'Gatsby 2' },
      {
        id: 5,
        credential_type: 4,
        kind: 'Machine',
        name: 'Cred 5',
        url: 'www.google.com',
      },
    ]);
  });

  test('should properly render vault credential labels', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <MultiCredentialsLookup
          value={credentials}
          tooltip="This is credentials look up"
          onChange={() => {}}
          onError={() => {}}
        />
      );
    });
    const searchButton = await waitForElement(
      wrapper,
      'Button[aria-label="Search"]'
    );
    await act(async () => {
      searchButton.invoke('onClick')();
    });
    wrapper.update();
    const typeSelect = wrapper.find('AnsibleSelect');
    act(() => {
      typeSelect.invoke('onChange')({}, 500);
    });
    wrapper.update();
    const optionsList = wrapper.find('OptionsList');
    expect(optionsList.prop('multiple')).toEqual(true);
    expect(wrapper.find('CheckboxListItem[label="Cred 6 | vault ID"]'));
    expect(wrapper.find('CheckboxListItem[label="Cred 7"]'));
  });

  test('should allow multiple vault credentials with no vault id', async () => {
    const onChange = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <MultiCredentialsLookup
          value={credentials}
          tooltip="This is credentials look up"
          onChange={onChange}
          onError={() => {}}
        />
      );
    });
    const searchButton = await waitForElement(
      wrapper,
      'Button[aria-label="Search"]'
    );
    await act(async () => {
      searchButton.invoke('onClick')();
    });
    wrapper.update();
    const typeSelect = wrapper.find('AnsibleSelect');
    act(() => {
      typeSelect.invoke('onChange')({}, 500);
    });
    wrapper.update();
    const optionsList = wrapper.find('OptionsList');
    expect(optionsList.prop('multiple')).toEqual(true);
    act(() => {
      optionsList.invoke('selectItem')({
        id: 11,
        credential_type: 3,
        kind: 'vault',
        name: 'Vault',
      });
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('Button[variant="primary"]').invoke('onClick')();
    });
    expect(onChange).toBeCalledWith([
      {
        id: 1,
        credential_type: 1,
        kind: 'gce',
        name: 'Foo',
        url: 'www.google.com',
      },
      {
        id: 2,
        credential_type: 2,
        kind: 'ssh',
        name: 'Alex',
        url: 'www.google.com',
      },
      {
        id: 21,
        credential_type: 3,
        kind: 'vault',
        inputs: { vault_id: '1' },
        name: 'Gatsby',
      },
      { id: 23, credential_type: 3, kind: 'vault', name: 'Gatsby 2' },
      { id: 8, credential_type: 4, kind: 'Machine', name: 'Gatsby' },
      { id: 11, credential_type: 3, kind: 'vault', name: 'Vault' },
    ]);
  });

  test('should allow multiple vault credentials with different vault ids', async () => {
    const onChange = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <MultiCredentialsLookup
          value={credentials}
          tooltip="This is credentials look up"
          onChange={onChange}
          onError={() => {}}
        />
      );
    });
    const searchButton = await waitForElement(
      wrapper,
      'Button[aria-label="Search"]'
    );
    await act(async () => {
      searchButton.invoke('onClick')();
    });
    wrapper.update();
    const typeSelect = wrapper.find('AnsibleSelect');
    act(() => {
      typeSelect.invoke('onChange')({}, 500);
    });
    wrapper.update();
    const optionsList = wrapper.find('OptionsList');
    expect(optionsList.prop('multiple')).toEqual(true);
    act(() => {
      optionsList.invoke('selectItem')({
        id: 12,
        credential_type: 3,
        kind: 'vault',
        name: 'Other Vault',
        vault_id: '2',
      });
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('Button[variant="primary"]').invoke('onClick')();
    });
    expect(onChange).toBeCalledWith([
      {
        id: 1,
        credential_type: 1,
        kind: 'gce',
        name: 'Foo',
        url: 'www.google.com',
      },
      {
        id: 2,
        credential_type: 2,
        kind: 'ssh',
        name: 'Alex',
        url: 'www.google.com',
      },
      {
        id: 21,
        credential_type: 3,
        kind: 'vault',
        inputs: { vault_id: '1' },
        name: 'Gatsby',
      },
      { id: 23, credential_type: 3, kind: 'vault', name: 'Gatsby 2' },
      { id: 8, credential_type: 4, kind: 'Machine', name: 'Gatsby' },
      {
        id: 12,
        credential_type: 3,
        kind: 'vault',
        name: 'Other Vault',
        vault_id: '2',
      },
    ]);
  });

  test('should not select multiple vault credentials with same vault id', async () => {
    const onChange = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <MultiCredentialsLookup
          value={credentials}
          tooltip="This is credentials look up"
          onChange={onChange}
          onError={() => {}}
        />
      );
    });
    const searchButton = await waitForElement(
      wrapper,
      'Button[aria-label="Search"]'
    );
    await act(async () => {
      searchButton.invoke('onClick')();
    });
    wrapper.update();
    const typeSelect = wrapper.find('AnsibleSelect');
    act(() => {
      typeSelect.invoke('onChange')({}, 500);
    });
    wrapper.update();
    const optionsList = wrapper.find('OptionsList');
    expect(optionsList.prop('multiple')).toEqual(true);
    act(() => {
      optionsList.invoke('selectItem')({
        id: 13,
        credential_type: 3,
        kind: 'vault',
        name: 'Vault Cred with Same Vault Id',
        inputs: { vault_id: '1' },
      });
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('Button[variant="primary"]').invoke('onClick')();
    });
    expect(onChange).toBeCalledWith([
      {
        id: 1,
        credential_type: 1,
        kind: 'gce',
        name: 'Foo',
        url: 'www.google.com',
      },
      {
        id: 2,
        credential_type: 2,
        kind: 'ssh',
        name: 'Alex',
        url: 'www.google.com',
      },
      { id: 23, credential_type: 3, kind: 'vault', name: 'Gatsby 2' },
      { id: 8, credential_type: 4, kind: 'Machine', name: 'Gatsby' },
      {
        id: 13,
        credential_type: 3,
        kind: 'vault',
        name: 'Vault Cred with Same Vault Id',
        inputs: { vault_id: '1' },
      },
    ]);
  });
});
