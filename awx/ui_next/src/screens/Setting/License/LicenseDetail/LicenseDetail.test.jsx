import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import LicenseDetail from './LicenseDetail';

describe('<LicenseDetail />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<LicenseDetail />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('LicenseDetail').length).toBe(1);
  });
});
