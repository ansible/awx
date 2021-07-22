import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { ApplicationsAPI } from 'api';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ApplicationLookup from './ApplicationLookup';

jest.mock('../../api');
const application = {
  id: 1,
  name: 'app',
  description: '',
};

const fetchedApplications = {
  count: 2,
  results: [
    {
      id: 1,
      name: 'app',
      description: '',
    },
    {
      id: 4,
      name: 'application that should not crach',
      description: '',
    },
  ],
};
describe('ApplicationLookup', () => {
  let wrapper;

  beforeEach(() => {
    ApplicationsAPI.read.mockResolvedValueOnce(fetchedApplications);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>
          <ApplicationLookup
            label="Application"
            value={application}
            onChange={() => {}}
          />
        </Formik>
      );
    });
    expect(wrapper.find('ApplicationLookup')).toHaveLength(1);
  });

  test('should fetch applications', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>
          <ApplicationLookup
            label="Application"
            value={application}
            onChange={() => {}}
          />
        </Formik>
      );
    });
    expect(ApplicationsAPI.read).toHaveBeenCalledTimes(1);
  });

  test('should display label', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik>
          <ApplicationLookup
            label="Application"
            value={application}
            onChange={() => {}}
          />
        </Formik>
      );
    });
    const title = wrapper.find('FormGroup .pf-c-form__label-text');
    expect(title.text()).toEqual('Application');
  });
});
