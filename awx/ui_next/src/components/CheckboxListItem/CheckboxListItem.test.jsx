import React from 'react';
import { mount } from 'enzyme';

import CheckboxListItem from './CheckboxListItem';

describe('CheckboxListItem', () => {
  test('renders the expected content', () => {
    const wrapper = mount(
      <table>
        <tbody>
          <CheckboxListItem
            itemId={1}
            name="Buzz"
            label="Buzz"
            isSelected={false}
            onSelect={() => {}}
            onDeselect={() => {}}
          />
        </tbody>
      </table>
    );
    expect(wrapper).toHaveLength(1);
  });
});
