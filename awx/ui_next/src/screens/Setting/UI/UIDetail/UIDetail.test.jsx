import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import UIDetail from './UIDetail';

describe('<UIDetail />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<UIDetail />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('UIDetail').length).toBe(1);
  });
});
