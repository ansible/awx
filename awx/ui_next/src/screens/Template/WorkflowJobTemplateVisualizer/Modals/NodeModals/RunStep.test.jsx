import React from 'react';
import { Formik } from 'formik';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../../../../testUtils/enzymeHelpers';
import RunStep from './RunStep';

let wrapper;

describe('RunStep', () => {
  beforeAll(() => {
    wrapper = mountWithContexts(
      <Formik initialValues={{ linkType: 'success' }}>
        <RunStep />
      </Formik>
    );
  });

  test('Default selected card matches default link type when present', () => {
    expect(wrapper.find('#link-type-success').props().isSelected).toBe(true);
    expect(wrapper.find('#link-type-failure').props().isSelected).toBe(false);
    expect(wrapper.find('#link-type-always').props().isSelected).toBe(false);
  });

  test('Clicking success card makes expected callback', async () => {
    await act(async () => wrapper.find('#link-type-always').simulate('click'));
    wrapper.update();
    expect(wrapper.find('#link-type-always').props().isSelected).toBe(true);
  });

  test('Clicking failure card makes expected callback', async () => {
    await act(async () => wrapper.find('#link-type-failure').simulate('click'));
    wrapper.update();
    expect(wrapper.find('#link-type-failure').props().isSelected).toBe(true);
  });
});
