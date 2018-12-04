import React from 'react';
import { mount } from 'enzyme';
import Tooltip from '../../src/components/Tooltip';

describe('<Tooltip />', () => {
  let wrapper;

  test('initially renders without crashing', () => {
    wrapper = mount(<Tooltip />);
    expect(wrapper.length).toBe(1);
  });
});
