import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
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
});
