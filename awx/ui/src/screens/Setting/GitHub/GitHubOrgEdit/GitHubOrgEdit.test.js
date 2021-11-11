import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { SettingsProvider } from 'contexts/Settings';
import { SettingsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../testUtils/enzymeHelpers';
import mockAllOptions from '../../shared/data.allSettingOptions.json';
import GitHubOrgEdit from './GitHubOrgEdit';

jest.mock('../../../../api');

describe('<GitHubOrgEdit />', () => {
  let wrapper;
  let history;

  beforeEach(() => {
    SettingsAPI.revertCategory.mockResolvedValue({});
    SettingsAPI.updateAll.mockResolvedValue({});
    SettingsAPI.readCategory.mockResolvedValue({
      data: {
        SOCIAL_AUTH_GITHUB_ORG_CALLBACK_URL:
          'https://towerhost/sso/complete/github-org/',
        SOCIAL_AUTH_GITHUB_ORG_KEY: '',
        SOCIAL_AUTH_GITHUB_ORG_SECRET: '$encrypted$',
        SOCIAL_AUTH_GITHUB_ORG_NAME: '',
        SOCIAL_AUTH_GITHUB_ORG_ORGANIZATION_MAP: null,
        SOCIAL_AUTH_GITHUB_ORG_TEAM_MAP: null,
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/settings/github/organization/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <GitHubOrgEdit />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  test('initially renders without crashing', () => {
    expect(wrapper.find('GitHubOrgEdit').length).toBe(1);
  });

  test('should display expected form fields', async () => {
    expect(
      wrapper.find('FormGroup[label="GitHub Organization OAuth2 Key"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="GitHub Organization OAuth2 Secret"]')
        .length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="GitHub Organization Name"]').length
    ).toBe(1);
    expect(
      wrapper.find(
        'FormGroup[label="GitHub Organization OAuth2 Organization Map"]'
      ).length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="GitHub Organization OAuth2 Team Map"]')
        .length
    ).toBe(1);
  });

  test('should successfully send default values to api on form revert all', async () => {
    expect(SettingsAPI.revertCategory).toHaveBeenCalledTimes(0);
    expect(wrapper.find('RevertAllAlert')).toHaveLength(0);
    await act(async () => {
      wrapper
        .find('button[aria-label="Revert all to default"]')
        .invoke('onClick')();
    });
    wrapper.update();
    expect(wrapper.find('RevertAllAlert')).toHaveLength(1);
    await act(async () => {
      wrapper
        .find('RevertAllAlert button[aria-label="Confirm revert all"]')
        .invoke('onClick')();
    });
    wrapper.update();
    expect(SettingsAPI.revertCategory).toHaveBeenCalledTimes(1);
    expect(SettingsAPI.revertCategory).toHaveBeenCalledWith('github-org');
  });

  test('should successfully send request to api on form submission', async () => {
    act(() => {
      wrapper
        .find(
          'FormGroup[fieldId="SOCIAL_AUTH_GITHUB_ORG_SECRET"] button[aria-label="Revert"]'
        )
        .invoke('onClick')();
      wrapper.find('input#SOCIAL_AUTH_GITHUB_ORG_NAME').simulate('change', {
        target: { value: 'new org', name: 'SOCIAL_AUTH_GITHUB_ORG_NAME' },
      });
      wrapper
        .find('CodeEditor#SOCIAL_AUTH_GITHUB_ORG_ORGANIZATION_MAP')
        .invoke('onChange')('{\n"Default":{\n"users":\nfalse\n}\n}');
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(1);
    expect(SettingsAPI.updateAll).toHaveBeenCalledWith({
      SOCIAL_AUTH_GITHUB_ORG_KEY: '',
      SOCIAL_AUTH_GITHUB_ORG_SECRET: '',
      SOCIAL_AUTH_GITHUB_ORG_NAME: 'new org',
      SOCIAL_AUTH_GITHUB_ORG_TEAM_MAP: null,
      SOCIAL_AUTH_GITHUB_ORG_ORGANIZATION_MAP: {
        Default: {
          users: false,
        },
      },
    });
  });

  test('should navigate to github organization detail on successful submission', async () => {
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(history.location.pathname).toEqual(
      '/settings/github/organization/details'
    );
  });

  test('should navigate to github organization detail when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual(
      '/settings/github/organization/details'
    );
  });

  test('should display error message on unsuccessful submission', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    SettingsAPI.updateAll.mockImplementation(() => Promise.reject(error));
    expect(wrapper.find('FormSubmitError').length).toBe(0);
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(0);
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(1);
  });

  test('should display ContentError on throw', async () => {
    SettingsAPI.readCategory.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <GitHubOrgEdit />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
