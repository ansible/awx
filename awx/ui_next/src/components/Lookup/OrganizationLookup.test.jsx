import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import OrganizationLookup, { _OrganizationLookup } from './OrganizationLookup';
import { OrganizationsAPI } from '../../api';

jest.mock('../../api');

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

  test('should auto-select organization when only one available and autoPopulate prop is true', async () => {
    OrganizationsAPI.read.mockReturnValue({
      data: {
        results: [{ id: 1 }],
        count: 1,
      },
    });
    const onChange = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationLookup autoPopulate onChange={onChange} />
      );
    });
    expect(onChange).toHaveBeenCalledWith({ id: 1 });
  });

  test('should not auto-select organization when autoPopulate prop is false', async () => {
    OrganizationsAPI.read.mockReturnValue({
      data: {
        results: [{ id: 1 }],
        count: 1,
      },
    });
    const onChange = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(<OrganizationLookup onChange={onChange} />);
    });
    expect(onChange).not.toHaveBeenCalled();
  });

  test('should not auto-select organization when multiple available', async () => {
    OrganizationsAPI.read.mockReturnValue({
      data: {
        results: [{ id: 1 }, { id: 2 }],
        count: 2,
      },
    });
    const onChange = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <OrganizationLookup autoPopulate onChange={onChange} />
      );
    });
    expect(onChange).not.toHaveBeenCalled();
  });
});
