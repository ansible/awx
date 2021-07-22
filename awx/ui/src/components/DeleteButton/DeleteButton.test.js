import React from 'react';
import { act } from 'react-dom/test-utils';
import { CredentialsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import DeleteButton from './DeleteButton';

jest.mock('../../api');

describe('<DeleteButton />', () => {
  test('should render button', () => {
    const wrapper = mountWithContexts(
      <DeleteButton onConfirm={() => {}} name="Foo" />
    );
    expect(wrapper.find('button')).toHaveLength(1);
  });

  test('should open confirmation modal', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <DeleteButton
          onConfirm={() => {}}
          name="Foo"
          deleteDetailsRequests={[
            {
              label: 'job',
              request: CredentialsAPI.read.mockResolvedValue({
                data: { count: 1 },
              }),
            },
          ]}
          deleteMessage="Delete this?"
          warningMessage="Are you sure to want to delete this"
        />
      );
    });

    await act(async () => {
      wrapper.find('button').prop('onClick')();
    });

    await waitForElement(wrapper, 'Modal', (el) => el.length > 0);
    expect(wrapper.find('Modal')).toHaveLength(1);

    expect(wrapper.find('div[aria-label="Delete this?"]')).toHaveLength(1);
  });

  test('should invoke onConfirm prop', async () => {
    const onConfirm = jest.fn();
    const wrapper = mountWithContexts(
      <DeleteButton
        onConfirm={onConfirm}
        itemsToDelete="foo"
        deleteDetailsRequests={[
          {
            label: 'job',
            request: CredentialsAPI.read.mockResolvedValue({
              data: { count: 1 },
            }),
          },
        ]}
        deleteMessage="Delete this?"
      />
    );
    await act(async () => wrapper.find('button').simulate('click'));
    wrapper.update();
    await act(async () =>
      wrapper
        .find('ModalBoxFooter button[aria-label="Confirm Delete"]')
        .simulate('click')
    );
    wrapper.update();
    expect(onConfirm).toHaveBeenCalled();
  });

  test('should show delete details error', async () => {
    const onConfirm = jest.fn();
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <DeleteButton
          onConfirm={onConfirm}
          itemsToDelete="foo"
          deleteDetailsRequests={[
            {
              label: 'job',
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
          ]}
        />
      );
    });
    await act(async () => wrapper.find('button').simulate('click'));
    wrapper.update();

    expect(wrapper.find('AlertModal[title="Error!"]')).toHaveLength(1);
  });
});
