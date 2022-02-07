import React from 'react';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../../../../testUtils/enzymeHelpers';
import DaysToKeepStep from './DaysToKeepStep';

let wrapper;

describe('DaysToKeepStep', () => {
  beforeAll(() => {
    wrapper = mountWithContexts(
      <Formik initialValues={{ daysToKeep: 30 }}>
        <DaysToKeepStep />
      </Formik>
    );
  });

  afterAll(() => {
    wrapper.unmount();
  });

  test('Days to keep field rendered correctly', () => {
    expect(wrapper.find('FormField#days-to-keep').length).toBe(1);
    expect(wrapper.find('FormField#days-to-keep').prop('isRequired')).toBe(
      true
    );
    expect(wrapper.find('input#days-to-keep').prop('value')).toBe(30);
  });
});
