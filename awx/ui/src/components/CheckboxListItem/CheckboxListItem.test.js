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

  test('should render row actions', () => {
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
            rowActions={[
              <div id="1">action_1</div>,
              <div id="2">action_2</div>,
            ]}
          />
        </tbody>
      </table>
    );
    expect(
      wrapper
        .find('ActionsTd')
        .containsAllMatchingElements([
          <div id="1">action_1</div>,
          <div id="2">action_2</div>,
        ])
    ).toEqual(true);
  });
});
