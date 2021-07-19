import React from 'react';
import { Link } from 'react-router-dom';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ActivityStreamDetailButton from './ActivityStreamDetailButton';

jest.mock('../../api/models/ActivityStream');

describe('<ActivityStreamDetailButton />', () => {
  test('initially renders successfully', () => {
    mountWithContexts(
      <ActivityStreamDetailButton
        streamItem={{
          timestamp: '12:00:00',
        }}
        user={<Link to="/users/1/details">Bob</Link>}
        description={<span>foo</span>}
      />
    );
  });
  test('details are properly rendered', () => {
    function assertDetail(label, value) {
      expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
      expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
    }

    const wrapper = mountWithContexts(
      <ActivityStreamDetailButton
        streamItem={{
          summary_fields: {
            actor: {
              id: 1,
              username: 'Bob',
              first_name: '',
              last_name: '',
            },
            setting: [
              {
                category: 'system',
                name: 'INSIGHTS_TRACKING_STATE',
              },
            ],
          },
          timestamp: '2021-05-25T18:17:59.835788Z',
          operation: 'create',
          changes: {
            value: false,
            id: 6,
          },
          object1: 'setting',
          object2: '',
          object_association: '',
          action_node: 'awx_1',
          object_type: '',
        }}
        user={<Link to="/users/1/details">Bob</Link>}
        description={<span>foo</span>}
      />
    );

    expect(wrapper.find('Modal[title="Event detail"]').prop('isOpen')).toBe(
      false
    );

    wrapper.find('Button').simulate('click');

    expect(wrapper.find('Modal[title="Event detail"]').prop('isOpen')).toBe(
      true
    );

    assertDetail('Time', '5/25/2021, 6:17:59 PM');
    assertDetail('Initiated by', 'Bob');
    assertDetail('Setting category', 'system');
    assertDetail('Setting name', 'INSIGHTS_TRACKING_STATE');
    assertDetail('Action', 'foo');

    const input = wrapper.find('VariablesDetail___StyledCodeEditor');
    expect(input).toHaveLength(1);
    expect(input.prop('value')).toEqual('{\n  "value": false,\n  "id": 6\n}');
  });
});
