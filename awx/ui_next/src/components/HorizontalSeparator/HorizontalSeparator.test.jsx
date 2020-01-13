import React from 'react';
import { mount } from 'enzyme';

import HorizontalSeparator from './HorizontalSeparator';

describe('HorizontalSeparator', () => {
  test('renders the expected content', () => {
    const wrapper = mount(<HorizontalSeparator />);
    expect(wrapper).toHaveLength(1);
  });
});
