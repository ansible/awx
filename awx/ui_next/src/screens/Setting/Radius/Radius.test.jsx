import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import Radius from './Radius';

describe('<Radius />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(<Radius />);
  });
  afterEach(() => {
    wrapper.unmount();
  });
  test('initially renders without crashing', () => {
    expect(wrapper.find('Card').text()).toContain('Radius settings');
  });
});
