import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../../../testUtils/enzymeHelpers';
import BecomeMethodField from './BecomeMethodField';

const fieldOptions = {
  help_text:
    "Specify a method for 'become' operations. This is equivalent to specifying the --become-method Ansible parameter.",
  id: 'become_method',
  label: 'Privilege Escalation Method',
  type: 'string',
};
describe('<BecomeMethodField>', () => {
  let wrapper;

  test('should mount properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>
          <BecomeMethodField fieldOptions={fieldOptions} isRequired />
        </Formik>
      );
    });
    expect(wrapper.find('BecomeMethodField').length).toBe(1);
  });

  test('should open privilege escalation properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>
          <BecomeMethodField fieldOptions={fieldOptions} isRequired />
        </Formik>
      );
    });
    act(() => wrapper.find('Select').prop('onToggle')(true));
    wrapper.update();
    expect(wrapper.find('SelectOption').length).toBe(12);
  });
});
