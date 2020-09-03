import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ApplicationLookup from './ApplicationLookup';
import { ApplicationsAPI } from '../../api';

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
    wrapper.unmount();
  });

  test('should render successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationLookup
          label="Application"
          value={application}
          onChange={() => {}}
        />
      );
    });
    expect(wrapper.find('ApplicationLookup')).toHaveLength(1);
  });

  test('should fetch applications', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationLookup
          label="Application"
          value={application}
          onChange={() => {}}
        />
      );
    });
    expect(ApplicationsAPI.read).toHaveBeenCalledTimes(1);
  });

  test('should display label', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ApplicationLookup
          label="Application"
          value={application}
          onChange={() => {}}
        />
      );
    });
    const title = wrapper.find('FormGroup .pf-c-form__label-text');
    expect(title.text()).toEqual('Application');
  });
});
