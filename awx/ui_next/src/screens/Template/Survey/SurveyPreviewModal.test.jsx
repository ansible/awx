import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  waitForElement,
  mountWithContexts,
} from '../../../../testUtils/enzymeHelpers';

import SurveyPreviewModal from './SurveyPreviewModal';

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

describe('<SurveyPreviewModal />', () => {
  let wrapper;
  beforeAll(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <SurveyPreviewModal questions={questions} isPreviewModalOpen />
      );
    });
    waitForElement(wrapper, 'Form');
  });
  afterAll(() => {
    wrapper.unmount();
  });
  test('renders successfully', async () => {
    expect(wrapper.find('SurveyPreviewModal').length).toBe(1);
  });

  test('Renders proper fields', async () => {
    const question1 = wrapper.find('FormGroup[label="Text Question"]');
    const question1Value = wrapper.find('TextInputBase').at(0);

    const question2 = wrapper
      .find('FormGroup[label="Select Question"]')
      .find('label');
    const question2Value = wrapper.find('Select[aria-label="Multiple Choice"]');

    const question3 = wrapper
      .find('FormGroup[label="Text Area Question"]')
      .find('label');
    const question3Value = wrapper.find('textarea');

    const question4 = wrapper.find('FormGroup[label="Password Question"]');
    const question4Value = wrapper.find('TextInputBase[type="password"]');

    const question5 = wrapper
      .find('FormGroup[label="Multiple select Question"]')
      .find('label');
    const question5Value = wrapper
      .find('Select[aria-label="Multi-Select"]')
      .find('Chip');

    expect(question1.text()).toBe('Text Question * ');
    expect(question1Value.prop('value')).toBe('Text Question Value');
    expect(question1Value.prop('isDisabled')).toBe(true);

    expect(question2.text()).toBe('Select Question *');
    expect(question2Value.find('.pf-c-select__toggle-text').text()).toBe(
      'Select Question Value'
    );
    expect(question2Value.prop('isDisabled')).toBe(true);

    expect(question3.text()).toBe('Text Area Question *');
    expect(question3Value.prop('value')).toBe('Text Area Question Value');
    expect(question3Value.prop('disabled')).toBe(true);
    expect(question4.text()).toBe('Password Question * ');
    expect(question4Value.prop('placeholder')).toBe('ENCRYPTED');
    expect(question4Value.prop('isDisabled')).toBe(true);

    expect(question5.text()).toBe('Multiple select Question *');
    expect(question5Value.length).toBe(4);
    expect(
      wrapper.find('Select[aria-label="Multi-Select"]').prop('isDisabled')
    ).toBe(true);
  });
});
