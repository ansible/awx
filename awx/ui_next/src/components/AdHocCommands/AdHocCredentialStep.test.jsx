import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import { CredentialsAPI } from '../../api';
import AdHocCredentialStep from './AdHocCredentialStep';

jest.mock('../../api/models/Credentials');

describe('<AdHocCredentialStep />', () => {
  const onEnableLaunch = jest.fn();
  let wrapper;
  beforeEach(async () => {
    CredentialsAPI.read.mockResolvedValue({
      data: {
        results: [
          { id: 1, name: 'Cred 1', url: 'wwww.google.com' },
          { id: 2, name: 'Cred2', url: 'wwww.google.com' },
        ],
        count: 2,
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>
          <AdHocCredentialStep
            credentialTypeId={1}
            onEnableLaunch={onEnableLaunch}
          />
        </Formik>
      );
    });
  });
  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('should mount properly', async () => {
    await waitForElement(wrapper, 'OptionsList', el => el.length > 0);
  });

  test('should call api', async () => {
    await waitForElement(wrapper, 'OptionsList', el => el.length > 0);
    expect(CredentialsAPI.read).toHaveBeenCalled();
    expect(wrapper.find('CheckboxListItem').length).toBe(2);
  });
});
