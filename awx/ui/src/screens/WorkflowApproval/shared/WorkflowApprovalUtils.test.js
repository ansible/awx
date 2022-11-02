import { I18nProvider } from '@lingui/react';
import { i18n } from '@lingui/core';
import { en } from 'make-plural/plurals';
import { formatDateString } from 'util/dates';
import {
  getPendingLabel,
  getStatus,
  getTooltip,
} from '../shared/WorkflowApprovalUtils';
import mockWorkflowApprovals from '../data.workflowApprovals.json';

const workflowApproval = mockWorkflowApprovals.results[0];
i18n.loadLocaleData('en', { plurals: en });

async function activate() {
  const { messages } = await import(`../../../locales/${'en'}/messages.js`);
  i18n.load('en', messages);
  i18n.activate('en');
}
activate();

describe('<WorkflowApproval />', () => {
  test('shows no expiration when approval status is pending and no approval_expiration', () => {
    expect(getPendingLabel(workflowApproval)).toEqual('Never expires');
  });

  test('shows expiration date/time when approval status is pending and approval_expiration present', () => {
    workflowApproval.approval_expiration = '2020-10-10T17:13:12.067947Z';

    expect(getPendingLabel(workflowApproval)).toEqual(
      `Expires on 10/10/2020, 5:13:12 PM`
    );
  });

  test('shows when an approval has timed out', () => {
    workflowApproval.status = 'failed';
    workflowApproval.timed_out = true;
    expect(getStatus(workflowApproval)).toEqual('timedOut');
  });

  test('shows when an approval has canceled', () => {
    workflowApproval.status = 'canceled';
    workflowApproval.canceled_on = '2020-10-10T17:13:12.067947Z';
    workflowApproval.timed_out = false;
    expect(getStatus(workflowApproval)).toEqual('canceled');
  });

  test('shows when an approval has beeen approved', () => {
    workflowApproval.summary_fields = {
      ...workflowApproval.summary_fields,
      approved_or_denied_by: { id: 1, username: 'Foobar' },
    };
    workflowApproval.status = 'successful';
    workflowApproval.canceled_on = '';
    workflowApproval.finished = '';
    expect(getStatus(workflowApproval)).toEqual('approved');
  });

  test('shows when an approval has timed out', () => {
    workflowApproval.summary_fields = {
      ...workflowApproval.summary_fields,
      approved_or_denied_by: { id: 1, username: 'Foobar' },
    };
    workflowApproval.status = 'failed';
    workflowApproval.finished = '';
    workflowApproval.failed = true;
    expect(getStatus(workflowApproval)).toEqual('denied');
  });

  test('shows correct approved tooltip with user', () => {
    workflowApproval.summary_fields = {
      ...workflowApproval.summary_fields,
      approved_or_denied_by: { id: 1, username: 'Foobar' },
    };
    workflowApproval.status = 'successful';
    workflowApproval.finished = '2020-10-10T17:13:12.067947Z';
    expect(getTooltip(workflowApproval)).toEqual(
      'Approved by Foobar - 10/10/2020, 5:13:12 PM'
    );
  });
  test('shows correct approved tooltip without user', () => {
    workflowApproval.summary_fields = {
      ...workflowApproval.summary_fields,
      approved_or_denied_by: {},
    };
    workflowApproval.status = 'successful';
    workflowApproval.finished = '2020-10-10T17:13:12.067947Z';
    expect(getTooltip(workflowApproval)).toEqual(
      'Approved - 10/10/2020, 5:13:12 PM.  See the Activity Stream for more information.'
    );
  });

  test('shows correct denial tooltip with user', () => {
    workflowApproval.summary_fields = {
      ...workflowApproval.summary_fields,
      approved_or_denied_by: { id: 1, username: 'Foobar' },
    };
    workflowApproval.status = 'failed';
    workflowApproval.finished = '2020-10-10T17:13:12.067947Z';
    workflowApproval.failed = true;
    expect(getTooltip(workflowApproval)).toEqual(
      'Denied by Foobar - 10/10/2020, 5:13:12 PM'
    );
  });
  test('shows correct denial tooltip without user', () => {
    workflowApproval.summary_fields = {
      ...workflowApproval.summary_fields,
      approved_or_denied_by: {},
    };
    workflowApproval.status = 'failed';
    workflowApproval.finished = '2020-10-10T17:13:12.067947Z';
    workflowApproval.failed = true;
    expect(getTooltip(workflowApproval)).toEqual(
      'Denied - 10/10/2020, 5:13:12 PM.  See the Activity Stream for more information.'
    );
  });
});
