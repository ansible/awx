import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import SurveyListItem from './SurveyListItem';

describe('<SurveyListItem />', () => {
  const item = { question_name: 'Foo', default: 'Bar', type: 'text', id: 1 };
  test('renders successfully', () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <SurveyListItem question={item} isFirst={false} isLast={false} />
      );
    });
    expect(wrapper.length).toBe(1);
  });
  test('fields are rendering properly', () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <SurveyListItem question={item} isFirst={false} isLast={false} />
      );
    });
    const moveUp = wrapper.find('Button[aria-label="move up"]');
    const moveDown = wrapper.find('Button[aria-label="move down"]');
    expect(moveUp.length).toBe(1);
    expect(moveDown.length).toBe(1);
    expect(
      wrapper
        .find('b')
        .at(0)
        .text()
    ).toBe('Type');
    expect(
      wrapper
        .find('b')
        .at(1)
        .text()
    ).toBe('Default');
    expect(wrapper.find('DataListCheck').length).toBe(1);
    expect(wrapper.find('DataListCell').length).toBe(3);
  });
  test('move up and move down buttons are disabled', () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <SurveyListItem question={item} isChecked={false} isFirst isLast />
      );
    });
    const moveUp = wrapper
      .find('Button[aria-label="move up"]')
      .prop('isDisabled');
    const moveDown = wrapper
      .find('Button[aria-label="move down"]')
      .prop('isDisabled');
    expect(moveUp).toBe(true);
    expect(moveDown).toBe(true);
  });
  test('required item has required asterisk', () => {
    const newItem = {
      question_name: 'Foo',
      default: 'Bar',
      type: 'text',
      id: 1,
      required: true,
    };

    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <SurveyListItem question={newItem} isChecked={false} isFirst isLast />
      );
    });
    expect(wrapper.find('span[aria-label="Required"]').length).toBe(1);
  });
  test('items that are not required should not have an asterisk', () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <SurveyListItem question={item} isChecked={false} isFirst isLast />
      );
    });
    expect(wrapper.find('span[aria-label="Required"]').length).toBe(0);
  });
  test('required item has required asterisk', () => {
    const newItem = {
      question_name: 'Foo',
      default: 'a\nd\nb\ne\nf\ng\nh\ni\nk',
      type: 'multiselect',
      id: 1,
    };

    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <SurveyListItem question={newItem} isChecked={false} isFirst isLast />
      );
    });
    expect(wrapper.find('Chip').length).toBe(6);
    wrapper
      .find('Chip')
      .filter(chip => chip.prop('isOverFlowChip') !== true)
      .map(chip => expect(chip.prop('isReadOnly')).toBe(true));
  });
  test('items that are no required should have no an asterisk', () => {
    const newItem = {
      question_name: 'Foo',
      default: '$encrypted$',
      type: 'password',
      id: 1,
    };

    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <SurveyListItem question={newItem} isChecked={false} isFirst isLast />
      );
    });
    expect(wrapper.find('span').text()).toBe('ENCRYPTED');
  });
  test('users without edit/delete permissions are unable to reorder the questions', () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <SurveyListItem
          question={item}
          canAddAndDelete={false}
          isChecked={false}
          isFirst
          isLast
        />
      );
    });
    expect(wrapper.find('button[aria-label="move up"]').prop('disabled')).toBe(
      true
    );
    expect(
      wrapper.find('button[aria-label="move down"]').prop('disabled')
    ).toBe(true);
  });
});
