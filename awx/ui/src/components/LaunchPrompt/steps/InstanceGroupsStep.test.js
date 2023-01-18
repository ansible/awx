import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { InstanceGroupsAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import InstanceGroupsStep from './InstanceGroupsStep';

jest.mock('../../../api/models/InstanceGroups');

const instance_groups = [
  { id: 1, name: 'ig one', url: '/instance_groups/1' },
  { id: 2, name: 'ig two', url: '/instance_groups/2' },
  { id: 3, name: 'ig three', url: '/instance_groups/3' },
];

describe('InstanceGroupsStep', () => {
  beforeEach(() => {
    InstanceGroupsAPI.read.mockResolvedValue({
      data: {
        results: instance_groups,
        count: 3,
      },
    });

    InstanceGroupsAPI.readOptions.mockResolvedValue({
      data: {
        actions: {
          GET: {},
          POST: {},
        },
        related_search_fields: [],
      },
    });
  });

  test('should load instance groups', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ instance_groups: [] }}>
          <InstanceGroupsStep />
        </Formik>
      );
    });
    wrapper.update();

    expect(InstanceGroupsAPI.read).toHaveBeenCalled();
    expect(wrapper.find('OptionsList').prop('options')).toEqual(
      instance_groups
    );
  });
});
