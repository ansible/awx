import React from 'react';
import { mount } from 'enzyme';
import Wizard from './Wizard';

describe('Wizard', () => {
  test('renders the expected content', () => {
    const wrapper = mount(<Wizard />);
    expect(wrapper).toMatchSnapshot();
  });
});
