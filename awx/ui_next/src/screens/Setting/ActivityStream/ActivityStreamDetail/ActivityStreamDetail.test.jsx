import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import ActivityStreamDetail from './ActivityStreamDetail';

describe('<ActivityStreamDetail />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<ActivityStreamDetail />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('ActivityStreamDetail').length).toBe(1);
  });
});
