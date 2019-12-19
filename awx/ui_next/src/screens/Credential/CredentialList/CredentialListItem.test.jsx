import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { CredentialListItem } from '.';
import mockCredentials from '../shared';

describe('<CredentialListItem />', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
  });

  test('edit button shown to users with edit capabilities', () => {
    wrapper = mountWithContexts(
      <CredentialListItem
        credential={mockCredentials.results[0]}
        detailUrl="/foo/bar"
        isSelected={false}
        onSelect={() => {}}
      />
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });

  test('edit button hidden from users without edit capabilities', () => {
    wrapper = mountWithContexts(
      <CredentialListItem
        credential={mockCredentials.results[1]}
        detailUrl="/foo/bar"
        isSelected={false}
        onSelect={() => {}}
      />
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });
});
