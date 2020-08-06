import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import LoggingDetail from './LoggingDetail';

describe('<LoggingDetail />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<LoggingDetail />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('LoggingDetail').length).toBe(1);
  });
});
