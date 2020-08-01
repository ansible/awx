import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../../../testUtils/enzymeHelpers';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../../../contexts/Workflow';
import LinkModal from './LinkModal';

const dispatch = jest.fn();
const onConfirm = jest.fn();
let wrapper;

describe('LinkModal', () => {
  describe('Adding new link', () => {
    beforeAll(() => {
      wrapper = mountWithContexts(
        <WorkflowDispatchContext.Provider value={dispatch}>
          <WorkflowStateContext.Provider
            value={{
              linkToEdit: null,
            }}
          >
            <LinkModal header="TEST" onConfirm={onConfirm} />
          </WorkflowStateContext.Provider>
        </WorkflowDispatchContext.Provider>
      );
    });

    afterAll(() => {
      wrapper.unmount();
    });

    test('Dropdown defaults to success when adding new link', () => {
      expect(wrapper.find('AnsibleSelect').prop('value')).toBe('success');
    });

    test('Cancel button dispatches as expected', () => {
      wrapper.find('button#link-cancel').simulate('click');
      expect(dispatch).toHaveBeenCalledWith({
        type: 'CANCEL_LINK_MODAL',
      });
    });

    test('Close button dispatches as expected', () => {
      wrapper.find('TimesIcon').simulate('click');
      expect(dispatch).toHaveBeenCalledWith({
        type: 'CANCEL_LINK_MODAL',
      });
    });

    test('Confirm button passes callback correct link type after changing dropdown', () => {
      act(() => {
        wrapper.find('AnsibleSelect').prop('onChange')(null, 'always');
      });
      wrapper.find('button#link-confirm').simulate('click');
      expect(onConfirm).toHaveBeenCalledWith('always');
    });
  });
  describe('Editing existing link', () => {
    test('Dropdown defaults to existing link type when editing link', () => {
      wrapper = mountWithContexts(
        <WorkflowDispatchContext.Provider value={dispatch}>
          <WorkflowStateContext.Provider
            value={{
              linkToEdit: {
                source: {
                  id: 2,
                },
                target: {
                  id: 3,
                },
                linkType: 'failure',
              },
            }}
          >
            <LinkModal header="TEST" onConfirm={onConfirm} />
          </WorkflowStateContext.Provider>
        </WorkflowDispatchContext.Provider>
      );
      expect(wrapper.find('AnsibleSelect').prop('value')).toBe('failure');
      wrapper.unmount();
    });
  });
});
