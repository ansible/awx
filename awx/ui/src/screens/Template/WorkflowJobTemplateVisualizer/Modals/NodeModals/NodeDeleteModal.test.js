import React from 'react';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from 'contexts/Workflow';
import { mountWithContexts } from '../../../../../../testUtils/enzymeHelpers';
import NodeDeleteModal from './NodeDeleteModal';

let wrapper;
const dispatch = jest.fn();

describe('NodeDeleteModal', () => {
  describe('Node with unified job template', () => {
    beforeAll(() => {
      wrapper = mountWithContexts(
        <WorkflowDispatchContext.Provider value={dispatch}>
          <WorkflowStateContext.Provider
            value={{
              nodeToDelete: {
                id: 2,
                unifiedJobTemplate: {
                  id: 4000,
                  name: 'Test JT',
                  type: 'job_template',
                },
                fullUnifiedJobTemplate: {
                  name: 'Bar',
                },
                originalNodeObject: {
                  identifier: '654160ef-4013-4b90-8e4b-87dee0cb6783',
                  summary_fields: { unified_job_template: { name: 'Bar' } },
                },
              },
            }}
          >
            <NodeDeleteModal />
          </WorkflowStateContext.Provider>
        </WorkflowDispatchContext.Provider>
      );
    });

    test('Mounts successfully', () => {
      expect(wrapper.length).toBe(1);
    });

    test('Confirm button dispatches as expected', () => {
      expect(wrapper.find('Title').text('Remove Node Bar'));
      wrapper.find('button#confirm-node-removal').simulate('click');
      expect(dispatch).toHaveBeenCalledWith({
        type: 'DELETE_NODE',
      });
    });

    test('Cancel button dispatches as expected', () => {
      wrapper.find('button#cancel-node-removal').simulate('click');
      expect(dispatch).toHaveBeenCalledWith({
        type: 'SET_NODE_TO_DELETE',
        value: null,
      });
    });

    test('Close button dispatches as expected', () => {
      wrapper.find('TimesIcon').simulate('click');
      expect(dispatch).toHaveBeenCalledWith({
        type: 'SET_NODE_TO_DELETE',
        value: null,
      });
    });
  });

  describe('Node without unified job template', () => {
    test('Mounts successfully', () => {
      wrapper = mountWithContexts(
        <WorkflowDispatchContext.Provider value={dispatch}>
          <WorkflowStateContext.Provider
            value={{
              nodeToDelete: {
                id: 2,
              },
            }}
          >
            <NodeDeleteModal />
          </WorkflowStateContext.Provider>
        </WorkflowDispatchContext.Provider>
      );
      expect(wrapper.length).toBe(1);
    });
  });
});
