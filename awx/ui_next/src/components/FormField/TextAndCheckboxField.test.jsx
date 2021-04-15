import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import TextAndCheckboxField from './TextAndCheckboxField';

describe('<TextAndCheckboxField/>', () => {
  test('should activate default values, multiselect', async () => {
    let wrapper;

    act(() => {
      wrapper = mountWithContexts(
        <Formik
          initialValues={{
            choices: 'alex\napollo\nathena',
            default: 'alex\napollo',
            type: 'multiselect',
          }}
        >
          <TextAndCheckboxField id="question-options" name="choices" />
        </Formik>
      );
    });
    await act(async () =>
      wrapper
        .find('TextAndCheckboxField')
        .find('TextAndCheckboxField')
        .find('TextInput')
        .at(0)
        .prop('onChange')('alex')
    );
    wrapper.update();
    expect(
      wrapper
        .find('Button[ouiaId="alex"]')
        .find('CheckIcon')
        .prop('isSelected')
    ).toBe(false);
    await act(() => wrapper.find('Button[ouiaId="alex"]').prop('onClick')());
    wrapper.update();
    expect(
      wrapper
        .find('Button[ouiaId="alex"]')
        .find('CheckIcon')
        .prop('isSelected')
    ).toBe(true);
    await act(async () =>
      wrapper
        .find('TextAndCheckboxField')
        .find('TextAndCheckboxField')
        .find('TextInput')
        .at(0)
        .prop('onKeyDown')({ key: 'Enter' })
    );
    wrapper.update();
    expect(wrapper.find('TextAndCheckboxField').find('InputGroup').length).toBe(
      3
    );
    await act(async () =>
      wrapper
        .find('TextAndCheckboxField')
        .find('TextAndCheckboxField')
        .find('TextInput')
        .at(1)
        .prop('onChange')('spencer')
    );
    wrapper.update();
    expect(wrapper.find('TextAndCheckboxField').find('InputGroup').length).toBe(
      3
    );
    await act(() => wrapper.find('Button[ouiaId="spencer"]').prop('onClick')());
    wrapper.update();
    expect(
      wrapper
        .find('Button[ouiaId="spencer"]')
        .find('CheckIcon')
        .prop('isSelected')
    ).toBe(true);
    await act(() => wrapper.find('Button[ouiaId="alex"]').prop('onClick')());
    wrapper.update();
    expect(
      wrapper
        .find('Button[ouiaId="alex"]')
        .find('CheckIcon')
        .prop('isSelected')
    ).toBe(false);
  });

  test('should select default, multiplechoice', async () => {
    let wrapper;

    act(() => {
      wrapper = mountWithContexts(
        <Formik
          initialValues={{
            choices: 'alex\napollo\nathena',
            default: 'alex\napollo',
            type: 'multiplechoice',
          }}
        >
          <TextAndCheckboxField id="question-options" name="choices" />
        </Formik>
      );
    });
    await act(async () =>
      wrapper
        .find('TextAndCheckboxField')
        .find('TextAndCheckboxField')
        .find('TextInput')
        .at(0)
        .prop('onChange')('alex')
    );
    wrapper.update();
    expect(
      wrapper
        .find('Button[ouiaId="alex"]')
        .find('CheckIcon')
        .prop('isSelected')
    ).toBe(false);
    await act(() => wrapper.find('Button[ouiaId="alex"]').prop('onClick')());
    wrapper.update();
    expect(
      wrapper
        .find('Button[ouiaId="alex"]')
        .find('CheckIcon')
        .prop('isSelected')
    ).toBe(true);
    expect(wrapper.find('TextAndCheckboxField').find('InputGroup').length).toBe(
      3
    );
    await act(async () =>
      wrapper
        .find('TextAndCheckboxField')
        .find('TextAndCheckboxField')
        .find('TextInput')
        .at(0)
        .prop('onKeyDown')({ key: 'Enter' })
    );
    wrapper.update();
    await act(async () =>
      wrapper
        .find('TextAndCheckboxField')
        .find('TextAndCheckboxField')
        .find('TextInput')
        .at(1)
        .prop('onChange')('spencer')
    );
    wrapper.update();
    expect(wrapper.find('TextAndCheckboxField').find('InputGroup').length).toBe(
      3
    );
    await act(() => wrapper.find('Button[ouiaId="spencer"]').prop('onClick')());
    wrapper.update();

    expect(
      wrapper
        .find('Button[ouiaId="spencer"]')
        .find('CheckIcon')
        .prop('isSelected')
    ).toBe(true);
    expect(
      wrapper
        .find('Button[ouiaId="alex"]')
        .find('CheckIcon')
        .prop('isSelected')
    ).toBe(false);
  });
});
