import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import OrganizationLookup, { _OrganizationLookup } from './OrganizationLookup';
import { OrganizationsAPI } from '@api';

jest.mock('@api');

describe('OrganizationLookup', () => {
  let wrapper;

  beforeEach(() => {
    wrapper = mountWithContexts(<OrganizationLookup onChange={() => {}} />);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders successfully', () => {
    expect(wrapper).toHaveLength(1);
  });
  test('should fetch organizations', () => {
    expect(OrganizationsAPI.read).toHaveBeenCalledTimes(1);
    expect(OrganizationsAPI.read).toHaveBeenCalledWith({
      order_by: 'name',
      page: 1,
      page_size: 5,
    });
  });
  test('should display "Organization" label', () => {
    const title = wrapper.find('FormGroup .pf-c-form__label-text');
    expect(title.text()).toEqual('Organization');
  });
  test('should define default value for function props', () => {
    expect(_OrganizationLookup.defaultProps.onBlur).toBeInstanceOf(Function);
    expect(_OrganizationLookup.defaultProps.onBlur).not.toThrow();
  });
});
