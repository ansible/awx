import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from 'contexts/Workflow';
import { useUserProfile } from 'contexts/Config';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../../testUtils/enzymeHelpers';
import NodeEditModal from './NodeEditModal';

const dispatch = jest.fn();

jest.mock('../../../../../api/models/InventorySources');
jest.mock('../../../../../api/models/JobTemplates');
jest.mock('../../../../../api/models/Projects');
jest.mock('../../../../../api/models/WorkflowJobTemplates');
const values = {
  inventory: undefined,
  nodeResource: {
    id: 448,
    name: 'Test JT',
    type: 'job_template',
  },
};

const workflowContext = {
  nodeToEdit: {
    id: 4,
    unifiedJobTemplate: {
      id: 30,
      name: 'Foo JT',
      type: 'job_template',
      unified_job_type: 'job',
    },
    originalNodeObject: {
      summary_fields: { unified_job_template: { id: 1, name: 'Job Template' } },
    },
  },
};

describe('NodeEditModal', () => {
  beforeEach(() => {
    useUserProfile.mockImplementation(() => {
      return {
        isSuperUser: true,
        isSystemAuditor: false,
        isOrgAdmin: false,
        isNotificationAdmin: false,
        isExecEnvAdmin: false,
      };
    });
  });
  test('Node modal confirmation dispatches as expected', async () => {
    const wrapper = mountWithContexts(
      <WorkflowDispatchContext.Provider value={dispatch}>
        <WorkflowStateContext.Provider value={workflowContext}>
          <NodeEditModal
            onSave={() => {}}
            askLinkType={false}
            title="Edit Node"
          />
        </WorkflowStateContext.Provider>
      </WorkflowDispatchContext.Provider>
    );
    waitForElement(
      wrapper,
      'WizardNavItem[content="ContentLoading"]',
      (el) => el.length === 0
    );
    await act(async () => {
      wrapper.find('NodeModal').prop('onSave')(values, {});
    });
    expect(dispatch).toHaveBeenCalledWith({
      node: {
        all_parents_must_converge: false,
        nodeResource: { id: 448, name: 'Test JT', type: 'job_template' },
      },
      type: 'UPDATE_NODE',
    });
  });
});
