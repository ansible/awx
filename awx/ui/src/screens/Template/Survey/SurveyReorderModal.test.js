import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  waitForElement,
  mountWithContexts,
} from '../../../../testUtils/enzymeHelpers';

import SurveyReorderModal from './SurveyReorderModal';

const questions = [
  {
    question_name: 'Text Question',
    question_description: '',
    required: true,
    type: 'text',
    variable: 'dfgh',
    min: 0,
    max: 1024,
    default: 'Text Question Value',
    choices: '',
  },
  {
    question_name: 'Select Question',
    question_description: '',
    required: true,
    type: 'multiplechoice',
    variable: 'sdf',
    min: null,
    max: null,
    default: 'Select Question Value',
    choices: 'a\nd\nc',
  },
  {
    question_name: 'Text Area Question',
    question_description: '',
    required: true,
    type: 'textarea',
    variable: 'b',
    min: 0,
    max: 4096,
    default: 'Text Area Question Value',
    choices: '',
  },
  {
    question_name: 'Password Question',
    question_description: '',
    required: true,
    type: 'password',
    variable: 'c',
    min: 0,
    max: 32,
    default: '$encrypted$',
    choices: '',
  },
  {
    question_name: 'Multiple select Question',
    question_description: '',
    required: true,
    type: 'multiselect',
    variable: 'a',
    min: null,
    max: null,
    default: 'a\nc\nd\nb',
    choices: 'a\nc\nd\nb',
  },
];

describe('<SurveyReorderModal />', () => {
  let wrapper;
  beforeAll(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <SurveyReorderModal questions={questions} isOrderModalOpen />
      );
    });
    waitForElement(wrapper, 'Form');
  });

  test('Renders proper fields', async () => {
    const question1 = wrapper.find('td[aria-label="Text Question"]');
    const question1Value = wrapper
      .find('TextInput#survey-preview-text-dfgh')
      .find('input');

    const question2 = wrapper.find('td[aria-label="Select Question"]');
    const question2Value = wrapper.find('Select[aria-label="Multiple Choice"]');

    const question3 = wrapper;
    wrapper.find('td[aria-label="Text Area Question"]');
    const question3Value = wrapper.find('textarea');

    const question4 = wrapper.find('td[aria-label="Password Question"]');
    const question4Value = wrapper.find('#survey-preview-encrypted');

    const question5 = wrapper.find('td[aria-label="Multiple select Question"]');
    const question5Value = wrapper
      .find('Select[aria-label="Multi-Select"]')
      .find('Chip');
    expect(question1).toHaveLength(1);
    expect(question1Value.prop('value')).toBe('Text Question Value');
    expect(question1Value.prop('disabled')).toBe(true);

    expect(question2).toHaveLength(1);
    expect(question2Value.prop('placeholderText')).toBe(
      'Select Question Value'
    );
    expect(question2Value.prop('isDisabled')).toBe(true);

    expect(question3).toHaveLength(1);
    expect(question3Value.prop('value')).toBe('Text Area Question Value');
    expect(question3Value.prop('disabled')).toBe(true);
    expect(question4).toHaveLength(1);
    expect(question4Value.prop('children')).toBe('ENCRYPTED');

    expect(question5).toHaveLength(1);
    expect(question5Value.length).toBe(4);
    expect(
      wrapper.find('Select[aria-label="Multi-Select"]').prop('isDisabled')
    ).toBe(true);
  });
});
