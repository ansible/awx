import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import OrganizationLookup, { _OrganizationLookup } from './OrganizationLookup';
import { OrganizationsAPI } from '@api';

jest.mock('@api');

describe('OrganizationLookup', () => {
  let wrapper;

  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('should render successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationLookup onChange={() => {}} />);
    });
    expect(wrapper).toHaveLength(1);
  });

  test('should fetch organizations', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationLookup onChange={() => {}} />);
    });
    expect(OrganizationsAPI.read).toHaveBeenCalledTimes(1);
    expect(OrganizationsAPI.read).toHaveBeenCalledWith({
      order_by: 'name',
      page: 1,
      page_size: 5,
    });
  });

  test('should display "Organization" label', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationLookup onChange={() => {}} />);
    });
    const title = wrapper.find('FormGroup .pf-c-form__label-text');
    expect(title.text()).toEqual('Organization');
  });

  test('should define default value for function props', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationLookup onChange={() => {}} />);
    });
    expect(_OrganizationLookup.defaultProps.onBlur).toBeInstanceOf(Function);
    expect(_OrganizationLookup.defaultProps.onBlur).not.toThrow();
  });
});
