import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import SurveyQuestionForm from './SurveyQuestionForm';

const question = {
  question_name: 'What is the foo?',
  question_description: 'more about the foo',
  variable: 'foo',
  required: true,
  type: 'text',
  min: 0,
  max: 1024,
};

const noop = () => {};

async function selectType(wrapper, type) {
  await act(async () => {
    wrapper.find('AnsibleSelect#question-type').invoke('onChange')({
      target: {
        name: 'type',
        value: type,
      },
    });
  });
  wrapper.update();
}

describe('<SurveyQuestionForm />', () => {
  test('should render form', () => {
    let wrapper;

    act(() => {
      wrapper = mountWithContexts(
        <SurveyQuestionForm
          question={question}
          handleSubmit={noop}
          handleCancel={noop}
        />
      );
    });

    expect(wrapper.find('FormField#question-name input').prop('value')).toEqual(
      question.question_name
    );
    expect(
      wrapper.find('FormField#question-description input').prop('value')
    ).toEqual(question.question_description);
    expect(
      wrapper.find('FormField#question-variable input').prop('value')
    ).toEqual(question.variable);
    expect(
      wrapper.find('CheckboxField#question-required input').prop('checked')
    ).toEqual(true);
    expect(wrapper.find('AnsibleSelect#question-type').prop('value')).toEqual(
      question.type
    );
  });

  test('should provide fields for text question', () => {
    let wrapper;

    act(() => {
      wrapper = mountWithContexts(
        <SurveyQuestionForm
          question={question}
          handleSubmit={noop}
          handleCancel={noop}
        />
      );
    });

    expect(wrapper.find('FormField#question-min').prop('type')).toEqual(
      'number'
    );
    expect(wrapper.find('FormField#question-max').prop('type')).toEqual(
      'number'
    );
    expect(wrapper.find('FormField#question-default').prop('type')).toEqual(
      'text'
    );
  });

  test('should provide fields for textarea question', async () => {
    let wrapper;

    act(() => {
      wrapper = mountWithContexts(
        <SurveyQuestionForm
          question={question}
          handleSubmit={noop}
          handleCancel={noop}
        />
      );
    });
    await selectType(wrapper, 'textarea');

    expect(wrapper.find('FormField#question-min').prop('type')).toEqual(
      'number'
    );
    expect(wrapper.find('FormField#question-max').prop('type')).toEqual(
      'number'
    );
    expect(wrapper.find('FormField#question-default').prop('type')).toEqual(
      'textarea'
    );
  });

  test('should provide fields for password question', async () => {
    let wrapper;

    act(() => {
      wrapper = mountWithContexts(
        <SurveyQuestionForm
          question={question}
          handleSubmit={noop}
          handleCancel={noop}
        />
      );
    });
    await selectType(wrapper, 'password');

    expect(wrapper.find('FormField#question-min').prop('type')).toEqual(
      'number'
    );
    expect(wrapper.find('FormField#question-max').prop('type')).toEqual(
      'number'
    );
    expect(
      wrapper.find('PasswordField#question-default input').prop('type')
    ).toEqual('password');
  });

  test('should provide fields for multiple choice question', async () => {
    let wrapper;

    act(() => {
      wrapper = mountWithContexts(
        <SurveyQuestionForm
          question={question}
          handleSubmit={noop}
          handleCancel={noop}
        />
      );
    });
    await selectType(wrapper, 'multiplechoice');

    expect(wrapper.find('FormField#question-options').prop('type')).toEqual(
      'textarea'
    );
    expect(wrapper.find('FormField#question-default').prop('type')).toEqual(
      'text'
    );
  });

  test('should provide fields for multi-select question', async () => {
    let wrapper;

    act(() => {
      wrapper = mountWithContexts(
        <SurveyQuestionForm
          question={question}
          handleSubmit={noop}
          handleCancel={noop}
        />
      );
    });
    await selectType(wrapper, 'multiselect');

    expect(wrapper.find('FormField#question-options').prop('type')).toEqual(
      'textarea'
    );
    expect(wrapper.find('FormField#question-default').prop('type')).toEqual(
      'textarea'
    );
  });

  test('should provide fields for integer question', async () => {
    let wrapper;

    act(() => {
      wrapper = mountWithContexts(
        <SurveyQuestionForm
          question={question}
          handleSubmit={noop}
          handleCancel={noop}
        />
      );
    });
    await selectType(wrapper, 'integer');

    expect(wrapper.find('FormField#question-min').prop('type')).toEqual(
      'number'
    );
    expect(wrapper.find('FormField#question-max').prop('type')).toEqual(
      'number'
    );
    expect(
      wrapper.find('FormField#question-default input').prop('type')
    ).toEqual('number');
  });

  test('should provide fields for float question', async () => {
    let wrapper;

    act(() => {
      wrapper = mountWithContexts(
        <SurveyQuestionForm
          question={question}
          handleSubmit={noop}
          handleCancel={noop}
        />
      );
    });
    await selectType(wrapper, 'float');

    expect(wrapper.find('FormField#question-min').prop('type')).toEqual(
      'number'
    );
    expect(wrapper.find('FormField#question-max').prop('type')).toEqual(
      'number'
    );
    expect(
      wrapper.find('FormField#question-default input').prop('type')
    ).toEqual('number');
  });
  test('should not throw validation error', async () => {
    let wrapper;

    act(() => {
      wrapper = mountWithContexts(
        <SurveyQuestionForm
          question={question}
          handleSubmit={noop}
          handleCancel={noop}
        />
      );
    });
    await selectType(wrapper, 'multiselect');
    await act(async () =>
      wrapper.find('textarea#question-options').simulate('change', {
        target: { value: 'a \n b', name: 'choices' },
      })
    );
    await act(async () =>
      wrapper.find('textarea#question-options').simulate('change', {
        target: { value: 'b \n a', name: 'default' },
      })
    );
    wrapper.find('FormField#question-default').prop('validate')('b \n a', {});
    wrapper.update();
    expect(
      wrapper
        .find('FormGroup[fieldId="question-default"]')
        .prop('helperTextInvalid')
    ).toBe(undefined);
  });

  test('should throw validation error', async () => {
    let wrapper;

    act(() => {
      wrapper = mountWithContexts(
        <SurveyQuestionForm
          question={question}
          handleSubmit={noop}
          handleCancel={noop}
        />
      );
    });
    await selectType(wrapper, 'multiselect');
    await act(async () =>
      wrapper.find('textarea#question-options').simulate('change', {
        target: { value: 'a \n b', name: 'choices' },
      })
    );
    await act(async () =>
      wrapper.find('textarea#question-default').simulate('change', {
        target: { value: 'c', name: 'default' },
      })
    );
    wrapper.find('FormField#question-default').prop('validate')('c', {});
    wrapper.update();
    expect(
      wrapper
        .find('FormGroup[fieldId="question-default"]')
        .prop('helperTextInvalid')
    ).toBe('Default choice must be answered from the choices listed.');
  });
});
