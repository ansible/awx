import React from 'react';
import { mountWithContexts } from '../../../../../../testUtils/enzymeHelpers';
import CredentialPluginPrompt from './CredentialPluginPrompt';

describe('<CredentialPluginPrompt />', () => {
  let wrapper;
  beforeAll(() => {
    wrapper = mountWithContexts(
      <CredentialPluginPrompt onClose={jest.fn()} onSubmit={jest.fn()} />
    );
  });
  afterAll(() => {
    wrapper.unmount();
  });
  test('renders the expected content', () => {
    expect(wrapper).toHaveLength(1);
  });
});
