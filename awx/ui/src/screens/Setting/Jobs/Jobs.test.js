import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { SettingsAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import mockJobSettings from '../shared/data.jobSettings.json';
import Jobs from './Jobs';

jest.mock('../../../api');

describe('<Jobs />', () => {
  let wrapper;

  beforeEach(() => {
    SettingsAPI.readCategory.mockResolvedValue({
      data: mockJobSettings,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render jobs details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/jobs/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<Jobs />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('JobsDetail').length).toBe(1);
  });

  test('should render jobs edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/jobs/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<Jobs />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('JobsEdit').length).toBe(1);
  });

  test('should show content error when user navigates to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/jobs/foo'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<Jobs />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
