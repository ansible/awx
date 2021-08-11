import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  shallowWithContexts,
} from '../../../../testUtils/enzymeHelpers';
import SurveyListItem from './SurveyListItem';

describe('<SurveyListItem />', () => {
  const item = {
    question_name: 'Foo',
    variable: 'buzz',
    default: 'Bar',
    type: 'text',
    id: 1,
  };

  test('renders successfully', () => {
    let wrapper;
    act(() => {
      wrapper = shallowWithContexts(
        <SurveyListItem question={item} isFirst={false} isLast={false} />
      );
    });
    expect(wrapper.length).toBe(1);
  });

  test('fields are rendering properly', () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <table>
          <tbody>
            <SurveyListItem
              question={item}
              isFirst={false}
              isLast={false}
              canEdit
            />
          </tbody>
        </table>
      );
    });
    expect(wrapper.find('SelectColumn').length).toBe(1);
    expect(wrapper.find('Td').length).toBe(5);
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
        <table>
          <tbody>
            <SurveyListItem
              question={newItem}
              isChecked={false}
              isFirst
              isLast
              canEdit
            />
          </tbody>
        </table>
      );
    });
    expect(wrapper.find('span[aria-label="Required"]').length).toBe(1);
  });
  test('items that are not required should not have an asterisk', () => {
    let wrapper;
    act(() => {
      wrapper = shallowWithContexts(
        <SurveyListItem
          question={item}
          isChecked={false}
          isFirst
          isLast
          canEdit
        />
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
        <table>
          <tbody>
            <SurveyListItem
              question={newItem}
              isChecked={false}
              isFirst
              isLast
              canEdit
            />
          </tbody>
        </table>
      );
    });
    expect(wrapper.find('Chip').length).toBe(6);
    wrapper
      .find('Chip')
      .filter((chip) => chip.prop('isOverFlowChip') !== true)
      .map((chip) => expect(chip.prop('isReadOnly')).toBe(true));
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
        <table>
          <tbody>
            <SurveyListItem
              question={newItem}
              isChecked={false}
              isFirst
              isLast
              canEdit
            />
          </tbody>
        </table>
      );
    });
    expect(wrapper.find('span').text()).toBe('ENCRYPTED');
  });

  test('users without edit/delete permissions are unable to reorder the questions', () => {
    let wrapper;
    act(() => {
      wrapper = shallowWithContexts(
        <SurveyListItem canEdit={false} question={item} isChecked={false} />
      );
    });
    expect(wrapper.find('button[aria-label="move up"]')).toHaveLength(0);
    expect(wrapper.find('button[aria-label="move down"]')).toHaveLength(0);
    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });

  test('edit button shown to users with edit capabilities', () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <table>
          <tbody>
            <SurveyListItem
              question={item}
              isFirst
              isLast
              isChecked={false}
              canEdit
            />
          </tbody>
        </table>
      );
    });

    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
    expect(wrapper.find('Button[ouiaId="edit-survey-buzz"]').prop('to')).toBe(
      'survey/edit?question_variable=buzz'
    );
  });
});
