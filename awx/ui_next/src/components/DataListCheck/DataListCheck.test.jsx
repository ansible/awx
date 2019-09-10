import React from 'react';
import { mount } from 'enzyme';
import DataListCheck from './DataListCheck';

describe('DataListCheck', () => {
  test('renders the expected content', () => {
    const wrapper = mount(<DataListCheck checked aria-labelledby="Checkbox" />);
    expect(wrapper).toHaveLength(1);
  });
});
