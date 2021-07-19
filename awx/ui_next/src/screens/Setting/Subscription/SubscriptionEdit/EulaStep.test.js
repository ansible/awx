import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import EulaStep from './EulaStep';

describe('<EulaStep />', () => {
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
          <EulaStep />
        </Formik>
      );
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders without crashing', async () => {
    expect(wrapper.find('EulaStep').length).toBe(1);
  });
});
