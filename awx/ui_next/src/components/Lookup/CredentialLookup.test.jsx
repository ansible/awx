import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import CredentialLookup, { _CredentialLookup } from './CredentialLookup';
import { CredentialsAPI } from '@api';

jest.mock('@api');

describe('CredentialLookup', () => {
  let wrapper;

  beforeEach(() => {
    wrapper = mountWithContexts(
      <CredentialLookup credentialTypeId={1} label="Foo" onChange={() => {}} />
    );
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders successfully', () => {
    expect(wrapper.find('CredentialLookup')).toHaveLength(1);
  });
  test('should fetch credentials', () => {
    expect(CredentialsAPI.read).toHaveBeenCalledTimes(1);
    expect(CredentialsAPI.read).toHaveBeenCalledWith({
      credential_type: 1,
      order_by: 'name',
      page: 1,
      page_size: 5,
    });
  });
  test('should display label', () => {
    const title = wrapper.find('FormGroup .pf-c-form__label-text');
    expect(title.text()).toEqual('Foo');
  });
  test('should define default value for function props', () => {
    expect(_CredentialLookup.defaultProps.onBlur).toBeInstanceOf(Function);
    expect(_CredentialLookup.defaultProps.onBlur).not.toThrow();
  });
});
