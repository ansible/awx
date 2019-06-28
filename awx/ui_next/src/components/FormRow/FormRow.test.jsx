import React from 'react';
import { mount } from 'enzyme';

import FormRow from './FormRow';

describe('FormRow', () => {
  test('renders the expected content', () => {
    const wrapper = mount(<FormRow />);
    expect(wrapper).toHaveLength(1);
  });
});
