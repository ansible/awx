import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import DisassociateButton from './DisassociateButton';

describe('<DisassociateButton />', () => {
  describe('User has disassociate permissions', () => {
    let wrapper;
    const handleDisassociate = jest.fn();
    const mockHosts = [
      {
        id: 1,
        name: 'foo',
        summary_fields: {
          user_capabilities: {
            delete: true,
          },
        },
      },
      {
        id: 2,
        name: 'bar',
        summary_fields: {
          user_capabilities: {
            delete: true,
          },
        },
      },
    ];

    beforeAll(() => {
      wrapper = mountWithContexts(
        <DisassociateButton
          onDisassociate={handleDisassociate}
          itemsToDisassociate={mockHosts}
          modalNote="custom note"
          modalTitle="custom title"
        />
      );
    });

    afterAll(() => {
      jest.clearAllMocks();
      wrapper.unmount();
    });

    test('should render button', () => {
      expect(wrapper.find('button')).toHaveLength(1);
      expect(wrapper.find('button').text()).toEqual('Disassociate');
    });

    test('should open confirmation modal', () => {
      wrapper.find('button').simulate('click');
      expect(wrapper.find('AlertModal')).toHaveLength(1);
    });

    test('cancel button should close confirmation modal', () => {
      expect(wrapper.find('AlertModal')).toHaveLength(1);
      wrapper.find('button[aria-label="Cancel"]').simulate('click');
      expect(wrapper.find('AlertModal')).toHaveLength(0);
    });

    test('should render expected modal content', () => {
      wrapper.find('button').simulate('click');
      expect(
        wrapper
          .find('AlertModal')
          .containsMatchingElement(<div>custom note</div>)
      ).toEqual(true);
      expect(
        wrapper
          .find('AlertModal')
          .containsMatchingElement(
            <div>This action will disassociate the following:</div>
          )
      ).toEqual(true);
      expect(wrapper.find('Title').text()).toEqual('custom title');
      wrapper.find('button[aria-label="Close"]').simulate('click');
    });

    test('disassociate button should call handleDisassociate on click', () => {
      wrapper.find('button').simulate('click');
      expect(handleDisassociate).toHaveBeenCalledTimes(0);
      wrapper
        .find('button[aria-label="confirm disassociate"]')
        .simulate('click');
      expect(handleDisassociate).toHaveBeenCalledTimes(1);
    });
  });

  describe('User does not have disassociate permissions', () => {
    const readOnlyHost = [
      {
        id: 1,
        name: 'foo',
        summary_fields: {
          user_capabilities: {
            delete: false,
          },
        },
      },
    ];

    test('should disable button when no delete permissions', () => {
      const wrapper = mountWithContexts(
        <DisassociateButton
          onDisassociate={() => {}}
          itemsToDelete={readOnlyHost}
        />
      );
      expect(wrapper.find('button[disabled]')).toHaveLength(1);
    });
  });
});
