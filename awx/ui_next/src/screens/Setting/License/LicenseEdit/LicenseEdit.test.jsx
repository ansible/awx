import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import LicenseEdit from './LicenseEdit';

describe('<LicenseEdit />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<LicenseEdit />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('LicenseEdit').length).toBe(1);
  });
});
