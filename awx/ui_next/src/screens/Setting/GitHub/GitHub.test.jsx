import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import GitHub from './GitHub';
import { SettingsAPI } from '../../../api';

jest.mock('../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({
  data: {},
});

describe('<GitHub />', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should render github details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/github/'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<GitHub />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('GitHubDetail').length).toBe(1);
  });

  test('should render github edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/github/default/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<GitHub />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('GitHubEdit').length).toBe(1);
  });

  test('should show content error when user navigates to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/github/foo/bar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<GitHub />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
