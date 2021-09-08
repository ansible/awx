import React from 'react';
import { shallow } from 'enzyme';
import useJobEvents from './useJobEvents';

const HookTest = ({ job = {} }) => {
  const hookObj = useJobEvents(job);
  return <div id="child" {...hookObj} />;
};

function getItem(wrapper, key) {
  return wrapper.find('#child').prop(key);
}

describe('useJobEvents', () => {
  describe('addEvents', () => {
    const newEvents = [
      {
        counter: 1,
        stdout: '',
        uuid: 'abc001',
      },
      {
        counter: 2,
        stdout: '',
        uuid: 'abc002',
      },
    ];

    test('should set events', () => {
      const wrapper = shallow(<HookTest />);
      expect(getItem(wrapper, 'events')).toEqual({});

      getItem(wrapper, 'addEvents')(newEvents);
      wrapper.update();
      expect(getItem(wrapper, 'events')).toEqual({
        0: newEvents[0],
        1: newEvents[1],
      });
    });

    test('should append events', () => {
      const extraEvents = [
        {
          counter: 3,
          stdout: '',
          uuid: 'abc003',
        },
      ];

      const wrapper = shallow(<HookTest />);
      expect(getItem(wrapper, 'events')).toEqual({});

      getItem(wrapper, 'addEvents')(newEvents);
      getItem(wrapper, 'addEvents')(extraEvents);
      wrapper.update();

      expect(getItem(wrapper, 'events')).toEqual({
        0: newEvents[0],
        1: newEvents[1],
        2: extraEvents[0],
      });
    });
  });

  describe('getEventForRow', () => {
    const newEvents = [
      {
        counter: 1,
        stdout: '',
        uuid: 'abc001',
      },
      {
        counter: 2,
        stdout: '',
        uuid: 'abc002',
      },
    ];
    test('should get first event', () => {
      const wrapper = shallow(<HookTest />);
      getItem(wrapper, 'addEvents')(newEvents);
      const node = getItem(wrapper, 'getEventForRow')(0);
      expect(node).toEqual({
        event: newEvents[0],
        firstChildIndex: 2,
        numChildren: null,
        isCollapsed: false,
      });
    });
  });
});
