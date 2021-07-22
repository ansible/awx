import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { WorkflowApprovalsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import WorkflowApprovals from './WorkflowApprovals';
import mockWorkflowApprovals from './data.workflowApprovals.json';

jest.mock('../../api');

describe('<WorkflowApprovals />', () => {
  beforeEach(() => {
    WorkflowApprovalsAPI.read.mockResolvedValue({
      data: {
        count: mockWorkflowApprovals.results.length,
        results: mockWorkflowApprovals.results,
      },
    });

    WorkflowApprovalsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
  });

  test('initially renders successfully', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<WorkflowApprovals />);
    });
    expect(wrapper.find('WorkflowApprovals').length).toBe(1);
  });

  test('should display a breadcrumb heading', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/workflow_approvals'],
    });
    const match = {
      path: '/workflow_approvals',
      url: '/workflow_approvals',
      isExact: true,
    };

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<WorkflowApprovals />, {
        context: {
          router: {
            history,
            route: {
              location: history.location,
              match,
            },
          },
        },
      });
    });

    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('Title').length).toBe(1);
  });
});
