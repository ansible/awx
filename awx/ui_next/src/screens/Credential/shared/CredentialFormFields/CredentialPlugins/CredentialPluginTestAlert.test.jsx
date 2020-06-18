import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import CredentialPluginTestAlert from './CredentialPluginTestAlert';

describe('<CredentialPluginTestAlert />', () => {
  let wrapper;
  afterEach(() => {
    wrapper.unmount();
  });
  test('renders expected content when test is successful', () => {
    wrapper = mountWithContexts(
      <CredentialPluginTestAlert
        credentialName="Foobar"
        successResponse={{}}
        errorResponse={null}
      />
    );
    expect(wrapper.find('b#credential-plugin-test-name').text()).toBe('Foobar');
    expect(wrapper.find('p#credential-plugin-test-message').text()).toBe(
      'Test passed'
    );
  });
  test('renders expected content when test fails with the expected return string formatting', () => {
    wrapper = mountWithContexts(
      <CredentialPluginTestAlert
        credentialName="Foobar"
        successResponse={null}
        errorResponse={{
          response: {
            data: {
              inputs: `HTTP 404
              {"errors":["not found"]}
              `,
            },
          },
        }}
      />
    );
    expect(wrapper.find('b#credential-plugin-test-name').text()).toBe('Foobar');
    expect(wrapper.find('p#credential-plugin-test-message').text()).toBe(
      'HTTP 404: not found'
    );
  });
  test('renders expected content when test fails without the expected return string formatting', () => {
    wrapper = mountWithContexts(
      <CredentialPluginTestAlert
        credentialName="Foobar"
        successResponse={null}
        errorResponse={{
          response: {
            data: {
              inputs: 'usernamee is not present at /secret/foo/bar/baz',
            },
          },
        }}
      />
    );
    expect(wrapper.find('b#credential-plugin-test-name').text()).toBe('Foobar');
    expect(wrapper.find('p#credential-plugin-test-message').text()).toBe(
      'usernamee is not present at /secret/foo/bar/baz'
    );
  });
});
