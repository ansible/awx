import React from 'react';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../../../contexts/Workflow';
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
              },
            }}
          >
            <NodeDeleteModal />
          </WorkflowStateContext.Provider>
        </WorkflowDispatchContext.Provider>
      );
    });

    afterAll(() => {
      wrapper.unmount();
    });

    test('Mounts successfully', () => {
      expect(wrapper.length).toBe(1);
    });

    test('Confirm button dispatches as expected', () => {
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
      wrapper.unmount();
    });
  });
});
