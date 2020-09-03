import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import MiscSystemDetail from './MiscSystemDetail';

describe('<MiscSystemDetail />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<MiscSystemDetail />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('MiscSystemDetail').length).toBe(1);
  });
});
