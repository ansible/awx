import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import AnalyticsStep from './AnalyticsStep';

describe('<AnalyticsStep />', () => {
  let wrapper;

  beforeEach(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik
          initialValues={{
            insights: false,
            manifest_file: null,
            manifest_filename: '',
            pendo: false,
            subscription: null,
            password: '',
            username: '',
          }}
        >
          <AnalyticsStep />
        </Formik>
      );
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders without crashing', async () => {
    expect(wrapper.find('AnalyticsStep').length).toBe(1);
  });
});
