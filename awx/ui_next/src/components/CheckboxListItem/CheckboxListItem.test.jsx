import React from 'react';
import { mount } from 'enzyme';

import CheckboxListItem from './CheckboxListItem';

describe('CheckboxListItem', () => {
  test('renders the expected content', () => {
    const wrapper = mount(
      <CheckboxListItem
        itemId={1}
        name="Buzz"
        label="Buzz"
        isSelected={false}
        onSelect={() => {}}
        onDeselect={() => {}}
      />
    );
    expect(wrapper).toHaveLength(1);
  });
});
