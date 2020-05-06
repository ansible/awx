import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import SurveyQuestionAdd from './SurveyQuestionAdd';

const survey = {
  spec: [
    {
      question_name: 'What is the foo?',
      question_description: 'more about the foo',
      variable: 'foo',
      required: true,
      type: 'text',
      min: 0,
      max: 1024,
    },
    {
      question_name: 'Who shot the sheriff?',
      question_description: 'they did not shoot the deputy',
      variable: 'bar',
      required: true,
      type: 'textarea',
      min: 0,
      max: 1024,
    },
  ],
};

describe('<SurveyQuestionAdd />', () => {
  let updateSurvey;

  beforeEach(() => {
    updateSurvey = jest.fn();
  });

  test('should render form', () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <SurveyQuestionAdd survey={survey} updateSurvey={updateSurvey} />
      );
    });

    expect(wrapper.find('SurveyQuestionForm')).toHaveLength(1);
  });

  test('should call updateSurvey', () => {
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <SurveyQuestionAdd survey={survey} updateSurvey={updateSurvey} />
      );
    });

    act(() => {
      wrapper.find('SurveyQuestionForm').invoke('handleSubmit')({
        question_name: 'new question',
        variable: 'question',
        type: 'text',
      });
    });
    wrapper.update();

    expect(updateSurvey).toHaveBeenCalledWith([
      ...survey.spec,
      {
        question_name: 'new question',
        variable: 'question',
        type: 'text',
      },
    ]);
  });

  test('should set formError', async () => {
    const realConsoleError = global.console.error;
    global.console.error = jest.fn();
    const err = new Error('oops');
    updateSurvey.mockImplementation(() => {
      throw err;
    });
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <SurveyQuestionAdd survey={survey} updateSurvey={updateSurvey} />
      );
    });

    act(() => {
      wrapper.find('SurveyQuestionForm').invoke('handleSubmit')({
        question_name: 'new question',
        variable: 'question',
        type: 'text',
      });
    });
    wrapper.update();

    expect(wrapper.find('SurveyQuestionForm').prop('submitError')).toEqual(err);
    global.console.error = realConsoleError;
  });

  test('should generate error for duplicate variable names', async () => {
    const realConsoleError = global.console.error;
    global.console.error = jest.fn();
    let wrapper;
    act(() => {
      wrapper = mountWithContexts(
        <SurveyQuestionAdd survey={survey} updateSurvey={updateSurvey} />
      );
    });

    act(() => {
      wrapper.find('SurveyQuestionForm').invoke('handleSubmit')({
        question_name: 'new question',
        variable: 'foo',
        type: 'text',
      });
    });
    wrapper.update();

    const err = wrapper.find('SurveyQuestionForm').prop('submitError');
    expect(err.message).toEqual(
      'Survey already contains a question with variable named “foo”'
    );
    global.console.error = realConsoleError;
  });
});
