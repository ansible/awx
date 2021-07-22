import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import MultipleChoiceField from './MultipleChoiceField';

describe('<MultipleChoiceField/>', () => {
  test('should activate default values, multiselect', async () => {
    let wrapper;

    act(() => {
      wrapper = mountWithContexts(
        <Formik
          initialValues={{
            formattedChoices: [
              { id: 1, choice: 'apollo', isDefault: true },
              { id: 2, choice: 'alex', isDefault: true },
              { id: 3, choice: 'athena', isDefault: false },
            ],
            type: 'multiselect',
          }}
        >
          <MultipleChoiceField id="question-options" name="choices" />
        </Formik>
      );
    });

    expect(
      wrapper
        .find('Button[ouiaId="alex-button"]')
        .find('CheckIcon')
        .prop('selected')
    ).toBe(true);
    await act(() =>
      wrapper.find('Button[ouiaId="alex-button"]').prop('onClick')()
    );
    wrapper.update();
    expect(
      wrapper
        .find('Button[ouiaId="alex-button"]')
        .find('CheckIcon')
        .prop('selected')
    ).toBe(false);
    await act(async () =>
      wrapper
        .find('MultipleChoiceField')
        .find('TextInput')
        .at(0)
        .prop('onKeyUp')({ key: 'Enter' })
    );
    wrapper.update();
    expect(wrapper.find('MultipleChoiceField').find('InputGroup').length).toBe(
      3
    );
    await act(async () =>
      wrapper
        .find('MultipleChoiceField')
        .find('TextInput')
        .at(2)
        .prop('onChange')('spencer')
    );
    wrapper.update();

    await act(() =>
      wrapper.find('Button[ouiaId="spencer-button"]').prop('onClick')()
    );
    wrapper.update();
    expect(
      wrapper
        .find('Button[ouiaId="spencer-button"]')
        .find('CheckIcon')
        .prop('selected')
    ).toBe(true);
    await act(() =>
      wrapper.find('Button[ouiaId="alex-button"]').prop('onClick')()
    );
    wrapper.update();
    expect(
      wrapper
        .find('Button[ouiaId="alex-button"]')
        .find('CheckIcon')
        .prop('selected')
    ).toBe(true);
  });

  test('should select default, multiplechoice', async () => {
    let wrapper;

    act(() => {
      wrapper = mountWithContexts(
        <Formik
          initialValues={{
            formattedChoices: [
              { choice: 'alex', isDefault: true, id: 1 },
              { choice: 'apollo', isDefault: false, id: 2 },
              { choice: 'athena', isDefault: false, id: 3 },
            ],
            type: 'multiplechoice',
          }}
        >
          <MultipleChoiceField id="question-options" name="choices" />
        </Formik>
      );
    });

    expect(
      wrapper
        .find('Button[ouiaId="alex-button"]')
        .find('CheckIcon')
        .prop('selected')
    ).toBe(true);
    await act(() =>
      wrapper.find('Button[ouiaId="alex-button"]').prop('onClick')()
    );
    wrapper.update();
    expect(
      wrapper
        .find('Button[ouiaId="alex-button"]')
        .find('CheckIcon')
        .prop('selected')
    ).toBe(false);
    expect(wrapper.find('MultipleChoiceField').find('InputGroup').length).toBe(
      3
    );
    await act(async () =>
      wrapper
        .find('MultipleChoiceField')
        .find('TextInput')
        .at(0)
        .prop('onKeyUp')({ key: 'Enter' })
    );
    wrapper.update();
    await act(async () =>
      wrapper
        .find('MultipleChoiceField')
        .find('TextInput')
        .at(2)
        .prop('onChange')('spencer')
    );
    wrapper.update();

    await act(() =>
      wrapper.find('Button[ouiaId="spencer-button"]').prop('onClick')()
    );
    wrapper.update();

    expect(
      wrapper
        .find('Button[ouiaId="spencer-button"]')
        .find('CheckIcon')
        .prop('selected')
    ).toBe(true);
    expect(
      wrapper
        .find('Button[ouiaId="alex-button"]')
        .find('CheckIcon')
        .prop('selected')
    ).toBe(false);
  });
});
