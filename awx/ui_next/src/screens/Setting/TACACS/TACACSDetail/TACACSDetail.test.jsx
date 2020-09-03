import React from 'react';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import TACACSDetail from './TACACSDetail';

describe('<TACACSDetail />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<TACACSDetail />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('TACACSDetail').length).toBe(1);
  });
});
