import React from 'react';
import { act } from 'react-dom/test-utils';
import { Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';

import { Formik } from 'formik';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import { CredentialsAPI } from '../../../api';

import WebhookSubForm from './WebhookSubForm';

jest.mock('../../../api');

describe('<WebhookSubForm />', () => {
  let wrapper;
  let history;
  const initialValues = {
    webhook_url: '/api/v2/job_templates/51/github/',
    webhook_credential: { id: 1, name: 'Github credential' },
    webhook_service: 'github',
    webhook_key: 'webhook key',
  };
  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['templates/job_template/51/edit'],
    });
    CredentialsAPI.read.mockResolvedValue({
      data: { results: [{ id: 12, name: 'Github credential' }] },
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route path="templates/:templateType/:id/edit">
          <Formik initialValues={initialValues}>
            <WebhookSubForm templateType="job_template" />
          </Formik>
        </Route>,
        {
          context: {
            router: {
              history,
              route: {
                location: { pathname: 'templates/job_template/51/edit' },
                match: { params: { id: 51, templateType: 'job_template' } },
              },
            },
          },
        }
      );
    });
  });
  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });
  test('mounts properly', () => {
    expect(wrapper.length).toBe(1);
  });
  test('should render initial values properly', () => {
    waitForElement(wrapper, 'Lookup__ChipHolder', el => el.lenth > 0);
    expect(wrapper.find('AnsibleSelect').prop('value')).toBe('github');
    expect(
      wrapper.find('TextInputBase[aria-label="Webhook URL"]').prop('value')
    ).toContain('/api/v2/job_templates/51/github/');
    expect(
      wrapper.find('TextInputBase[aria-label="wfjt-webhook-key"]').prop('value')
    ).toBe('webhook key');
    expect(
      wrapper
        .find('Chip')
        .find('span')
        .text()
    ).toBe('Github credential');
  });
  test('should make other credential type available', async () => {
    CredentialsAPI.read.mockResolvedValue({
      data: { results: [{ id: 13, name: 'GitLab credential' }] },
    });
    await act(async () =>
      wrapper.find('AnsibleSelect').prop('onChange')({}, 'gitlab')
    );
    expect(CredentialsAPI.read).toHaveBeenCalledWith({
      namespace: 'gitlab_token',
    });
    wrapper.update();
    expect(
      wrapper.find('TextInputBase[aria-label="Webhook URL"]').prop('value')
    ).toContain('/api/v2/job_templates/51/gitlab/');
    expect(
      wrapper.find('TextInputBase[aria-label="wfjt-webhook-key"]').prop('value')
    ).toBe('A NEW WEBHOOK KEY WILL BE GENERATED ON SAVE.');
  });
  test('should have disabled button to update webhook key', async () => {
    let newWrapper;
    await act(async () => {
      newWrapper = mountWithContexts(
        <Route path="templates/:templateType/:id/edit">
          <Formik
            initialValues={{
              ...initialValues,
              webhook_key: 'A NEW WEBHOOK KEY WILL BE GENERATED ON SAVE.',
            }}
          >
            <WebhookSubForm templateType="job_template" />
          </Formik>
        </Route>,
        {
          context: {
            router: {
              history,
              route: {
                location: { pathname: 'templates/job_template/51/edit' },
                match: { params: { id: 51, templateType: 'job_template' } },
              },
            },
          },
        }
      );
    });
    expect(
      newWrapper
        .find("Button[aria-label='Update webhook key']")
        .prop('isDisabled')
    ).toBe(true);
  });

  test('test whether the workflow template type is part of the webhook url', async () => {
    let newWrapper;
    const webhook_url = '/api/v2/workflow_job_templates/42/github/';
    await act(async () => {
      newWrapper = mountWithContexts(
        <Route path="templates/:templateType/:id/edit">
          <Formik initialValues={{ ...initialValues, webhook_url }}>
            <WebhookSubForm templateType="workflow_job_template" />
          </Formik>
        </Route>,
        {
          context: {
            router: {
              history,
              route: {
                location: {
                  pathname: 'templates/workflow_job_template/51/edit',
                },
                match: {
                  params: { id: 51, templateType: 'workflow_job_template' },
                },
              },
            },
          },
        }
      );
    });
    expect(
      newWrapper.find('TextInputBase[aria-label="Webhook URL"]').prop('value')
    ).toContain(webhook_url);
  });
});
