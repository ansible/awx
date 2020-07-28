import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import JobsDetail from './JobsDetail';

describe('<JobsDetail />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<JobsDetail />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('JobsDetail').length).toBe(1);
  });
});
