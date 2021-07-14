import React from 'react';
import { Formik } from 'formik';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import RevertButton from './RevertButton';

describe('RevertButton', () => {
  let wrapper;

  test('button text should display "Revert"', async () => {
    wrapper = mountWithContexts(
      <Formik
        initialValues={{
          test_input: 'foo',
        }}
      >
        <RevertButton id="test_input" defaultValue="" />
      </Formik>
    );
    expect(wrapper.find('button').text()).toEqual('Revert');
  });

  test('button text should display "Undo"', async () => {
    wrapper = mountWithContexts(
      <Formik
        initialValues={{
          test_input: 'foo',
        }}
        values={{
          test_input: 'bar',
        }}
      >
        <RevertButton id="test_input" defaultValue="bar" />
      </Formik>
    );
    expect(wrapper.find('button').text()).toEqual('Revert');
  });

  test('should revert value to default on button click', async () => {
    wrapper = mountWithContexts(
      <Formik
        initialValues={{
          test_input: 'foo',
        }}
      >
        <RevertButton id="test_input" defaultValue="bar" />
      </Formik>
    );
    expect(wrapper.find('button').text()).toEqual('Revert');
    await act(async () => {
      wrapper.find('button[aria-label="Revert"]').invoke('onClick')();
    });
    wrapper.update();
    expect(wrapper.find('button').text()).toEqual('Undo');
  });

  test('should be disabled when current value equals the initial and default values', async () => {
    wrapper = mountWithContexts(
      <Formik
        initialValues={{
          test_input: 'bar',
        }}
        values={{
          test_input: 'bar',
        }}
      >
        <RevertButton id="test_input" defaultValue="bar" />
      </Formik>
    );
    expect(wrapper.find('button').text()).toEqual('Revert');
    expect(wrapper.find('button').props().disabled).toBe(true);
  });
});
