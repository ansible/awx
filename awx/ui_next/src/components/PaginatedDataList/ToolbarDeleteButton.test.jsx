import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import { CredentialsAPI } from '../../api';
import ToolbarDeleteButton from './ToolbarDeleteButton';

jest.mock('../../api');

const itemA = {
  id: 1,
  name: 'Foo',
  summary_fields: { user_capabilities: { delete: true } },
};
const itemB = {
  id: 1,
  name: 'Foo',
  summary_fields: { user_capabilities: { delete: false } },
};
const itemC = {
  id: 1,
  username: 'Foo',
  summary_fields: { user_capabilities: { delete: false } },
};

describe('<ToolbarDeleteButton />', () => {
  let deleteDetailsRequests;
  beforeEach(() => {
    deleteDetailsRequests = [
      {
        label: 'Workflow Job Template Node',
        request: CredentialsAPI.read.mockResolvedValue({ data: { count: 1 } }),
      },
    ];
  });
  test('should render button', () => {
    const wrapper = mountWithContexts(
      <ToolbarDeleteButton onDelete={() => {}} itemsToDelete={[]} />
    );
    expect(wrapper.find('button')).toHaveLength(1);
    expect(wrapper.find('ToolbarDeleteButton')).toMatchSnapshot();
  });

  test('should open confirmation modal', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <ToolbarDeleteButton
          onDelete={() => {}}
          itemsToDelete={[itemA]}
          deleteDetailsRequests={deleteDetailsRequests}
          deleteMessage="Delete this?"
          warningMessage="Are you sure to want to delete this"
        />
      );
    });

    expect(wrapper.find('Modal')).toHaveLength(0);
    await act(async () => {
      wrapper.find('button').prop('onClick')();
    });
    await waitForElement(wrapper, 'Modal', el => el.length > 0);
    expect(CredentialsAPI.read).toBeCalled();
    expect(wrapper.find('Modal')).toHaveLength(1);
    expect(
      wrapper.find('span[aria-label="Workflow Job Template Node: 1"]')
    ).toHaveLength(1);
    expect(wrapper.find('div[aria-label="Delete this?"]')).toHaveLength(1);
  });

  test('should open delete error modal', async () => {
    const request = [
      {
        label: 'Workflow Job Template Node',
        request: CredentialsAPI.read.mockRejectedValue(
          new Error({
            response: {
              config: {
                method: 'get',
                url: '/api/v2/credentals',
              },
              data: 'An error occurred',
              status: 403,
            },
          })
        ),
      },
    ];
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <ToolbarDeleteButton
          onDelete={() => {}}
          itemsToDelete={[itemA]}
          deleteDetailsRequests={request}
          deleteMessage="Delete this?"
          warningMessage="Are you sure to want to delete this"
        />
      );
    });

    expect(wrapper.find('Modal')).toHaveLength(0);
    await act(async () => wrapper.find('button').simulate('click'));
    await waitForElement(wrapper, 'Modal', el => el.length > 0);
    expect(CredentialsAPI.read).toBeCalled();

    wrapper.update();

    expect(wrapper.find('AlertModal[title="Error!"]')).toHaveLength(1);
  });

  test('should invoke onDelete prop', () => {
    const onDelete = jest.fn();
    const wrapper = mountWithContexts(
      <ToolbarDeleteButton onDelete={onDelete} itemsToDelete={[itemA]} />
    );
    wrapper.find('button').simulate('click');
    wrapper.update();
    wrapper
      .find('ModalBoxFooter button[aria-label="confirm delete"]')
      .simulate('click');
    wrapper.update();
    expect(onDelete).toHaveBeenCalled();
    expect(wrapper.find('Modal')).toHaveLength(0);
  });

  test('should disable button when no delete permissions', () => {
    const wrapper = mountWithContexts(
      <ToolbarDeleteButton onDelete={() => {}} itemsToDelete={[itemB]} />
    );
    expect(wrapper.find('button[disabled]')).toHaveLength(1);
  });

  test('should render tooltip', () => {
    const wrapper = mountWithContexts(
      <ToolbarDeleteButton onDelete={() => {}} itemsToDelete={[itemA]} />
    );
    expect(wrapper.find('Tooltip')).toHaveLength(1);
    expect(wrapper.find('Tooltip').prop('content')).toEqual('Delete');
  });

  test('should render tooltip for username', () => {
    const wrapper = mountWithContexts(
      <ToolbarDeleteButton onDelete={() => {}} itemsToDelete={[itemC]} />
    );
    expect(wrapper.find('Tooltip')).toHaveLength(1);
    expect(wrapper.find('Tooltip').prop('content').props.children).toEqual(
      'You do not have permission to delete Items: Foo'
    );
  });
});
