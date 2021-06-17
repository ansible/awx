import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import SurveyStep from './SurveyStep';

describe('SurveyStep', () => {
  test('should handle choices as a string', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ job_type: 'run' }}>
          <SurveyStep
            surveyConfig={{
              name: 'survey',
              description: '',
              spec: [
                {
                  question_name: 'q1',
                  question_description: '',
                  required: true,
                  type: 'multiplechoice',
                  variable: 'q1',
                  min: null,
                  max: null,
                  default: '',
                  choices: '1\n2\n3\n4\n5\n6',
                },
              ],
            }}
          />
        </Formik>
      );
    });

    await act(async () => {
      wrapper.find('SelectToggle').simulate('click');
    });
    wrapper.update();
    const selectOptions = wrapper.find('SelectOption');
    expect(selectOptions.at(0).prop('value')).toEqual('1');
    expect(selectOptions.at(1).prop('value')).toEqual('2');
    expect(selectOptions.at(2).prop('value')).toEqual('3');
    expect(selectOptions.at(3).prop('value')).toEqual('4');
    expect(selectOptions.at(4).prop('value')).toEqual('5');
    expect(selectOptions.at(5).prop('value')).toEqual('6');
  });
  test('should handle choices as an array', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ job_type: 'run' }}>
          <SurveyStep
            surveyConfig={{
              name: 'survey',
              description: '',
              spec: [
                {
                  question_name: 'q1',
                  question_description: '',
                  required: true,
                  type: 'multiplechoice',
                  variable: 'q1',
                  min: null,
                  max: null,
                  default: '',
                  choices: ['1', '2', '3', '4', '5', '6'],
                },
              ],
            }}
          />
        </Formik>
      );
    });

    await act(async () => {
      wrapper.find('SelectToggle').simulate('click');
    });
    wrapper.update();
    const selectOptions = wrapper.find('SelectOption');
    expect(selectOptions.at(0).prop('value')).toEqual('1');
    expect(selectOptions.at(1).prop('value')).toEqual('2');
    expect(selectOptions.at(2).prop('value')).toEqual('3');
    expect(selectOptions.at(3).prop('value')).toEqual('4');
    expect(selectOptions.at(4).prop('value')).toEqual('5');
    expect(selectOptions.at(5).prop('value')).toEqual('6');
  });
});
