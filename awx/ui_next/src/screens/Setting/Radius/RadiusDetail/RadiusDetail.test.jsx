import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import RadiusDetail from './RadiusDetail';

describe('<RadiusDetail />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<RadiusDetail />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('RadiusDetail').length).toBe(1);
  });
});
