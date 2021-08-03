import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { WorkflowApprovalsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import mockWorkflowApprovals from './data.workflowApprovals.json';
import WorkflowApproval from './WorkflowApproval';

jest.mock('../../api');

const mockMe = {
  is_super_user: true,
  is_system_auditor: false,
};

describe('<WorkflowApproval />', () => {
  beforeEach(() => {
    WorkflowApprovalsAPI.readDetail.mockResolvedValue({
      data: mockWorkflowApprovals.results[0],
    });
  });

  test('initially renders successfully', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowApproval setBreadcrumb={() => {}} me={mockMe} />
      );
    });
    expect(wrapper.find('WorkflowApproval').length).toBe(1);
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/workflow_approvals/1/foobar'],
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <WorkflowApproval setBreadcrumb={() => {}} me={mockMe} />,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: {
                  params: { id: 1 },
                  url: '/workflow_approvals/1/foobar',
                  path: '/workflow_approvals/1/foobar',
                },
              },
            },
          },
        }
      );
    });
    await waitForElement(wrapper, 'ContentError', (el) => el.length === 1);
  });
});
