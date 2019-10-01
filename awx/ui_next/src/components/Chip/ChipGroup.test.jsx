import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import { ChipGroup, Chip } from '.';

describe('<ChipGroup />', () => {
  test('should render all chips', () => {
    const wrapper = mountWithContexts(
      <ChipGroup>
        <Chip>One</Chip>
        <Chip>Two</Chip>
        <Chip>Three</Chip>
        <Chip>Four</Chip>
        <Chip>Five</Chip>
        <Chip>Six</Chip>
      </ChipGroup>
    );
    expect(wrapper.find(Chip)).toHaveLength(6);
    expect(wrapper.find('li')).toHaveLength(6);
  });

  test('should render show more toggle', () => {
    const wrapper = mountWithContexts(
      <ChipGroup showOverflowAfter={5}>
        <Chip>One</Chip>
        <Chip>Two</Chip>
        <Chip>Three</Chip>
        <Chip>Four</Chip>
        <Chip>Five</Chip>
        <Chip>Six</Chip>
        <Chip>Seven</Chip>
      </ChipGroup>
    );
    expect(wrapper.find(Chip)).toHaveLength(6);
    const toggle = wrapper.find(Chip).at(5);
    expect(toggle.prop('isOverflowChip')).toBe(true);
    expect(toggle.text()).toEqual('2 more');
  });

  test('should render show less toggle', () => {
    const wrapper = mountWithContexts(
      <ChipGroup showOverflowAfter={5}>
        <Chip>One</Chip>
        <Chip>Two</Chip>
        <Chip>Three</Chip>
        <Chip>Four</Chip>
        <Chip>Five</Chip>
        <Chip>Six</Chip>
        <Chip>Seven</Chip>
      </ChipGroup>
    );
    expect(wrapper.find(Chip)).toHaveLength(6);
    const toggle = wrapper.find(Chip).at(5);
    expect(toggle.prop('isOverflowChip')).toBe(true);
    act(() => {
      toggle.prop('onClick')();
    });
    wrapper.update();
    expect(wrapper.find(Chip)).toHaveLength(8);
    expect(
      wrapper
        .find(Chip)
        .at(7)
        .text()
    ).toEqual('Show Less');
    act(() => {
      const toggle2 = wrapper.find(Chip).at(7);
      expect(toggle2.prop('isOverflowChip')).toBe(true);
      toggle2.prop('onClick')();
    });
    wrapper.update();
    expect(wrapper.find(Chip)).toHaveLength(6);
  });
});
