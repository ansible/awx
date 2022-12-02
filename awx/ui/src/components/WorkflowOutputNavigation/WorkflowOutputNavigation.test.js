import React from 'react';
import { within, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import WorkflowOutputNavigation from './WorkflowOutputNavigation';
import { createMemoryHistory } from 'history';
import { I18nProvider } from '@lingui/react';
import { i18n } from '@lingui/core';
import { en } from 'make-plural/plurals';
import english from '../../../src/locales/en/messages';
import { Router } from 'react-router-dom';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 1,
  }),
}));
const jobs = [
  {
    id: 1,
    summary_fields: {
      job: {
        name: 'Ansible',
        type: 'project_update',
        id: 1,
        status: 'successful',
      },
    },
    job: 4,
  },
  {
    id: 2,
    summary_fields: {
      job: {
        name: 'Durham',
        type: 'job',
        id: 2,
        status: 'successful',
      },
    },
    job: 3,
  },
  {
    id: 3,
    summary_fields: {
      job: {
        name: 'Red hat',
        type: 'job',
        id: 3,
        status: 'successful',
      },
    },
    job: 2,
  },
];

describe('<WorkflowOuputNavigation/>', () => {
  test('Should open modal and deprovision node', async () => {
    i18n.loadLocaleData({ en: { plurals: en } });
    i18n.load({ en: english });
    i18n.activate('en');
    const user = userEvent.setup();
    const ref = jest
      .spyOn(React, 'useRef')
      .mockReturnValueOnce({ current: 'div' });
    const history = createMemoryHistory({
      initialEntries: ['jobs/playbook/2/output'],
    });
    render(
      <I18nProvider i18n={i18n}>
        <Router history={history}>
          <WorkflowOutputNavigation relatedJobs={jobs} parentRef={ref} />
        </Router>
      </I18nProvider>
    );

    const button = screen.getByRole('button');
    await user.click(button);

    await waitFor(() => screen.getByText('Workflow Nodes'));
    await waitFor(() => screen.getByText('Red hat'));
    await waitFor(() => screen.getByText('Durham'));
    await waitFor(() => screen.getByText('Ansible'));
  });
});
