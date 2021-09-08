import { useState } from 'react';
import getLineTextHtml from './getLineTextHtml';

function normalizeEvents(job, events) {
  let countOffset = 0;
  if (!job?.result_traceback) {
    return {
      events,
      countOffset,
    };
  }

  const tracebackEvent = {
    counter: 1,
    created: null,
    event: null,
    type: null,
    stdout: job?.result_traceback,
    start_line: 0,
  };
  // TODO: set as event at index 0 and use exact counter as index in addEvents?
  const firstIndex = events.findIndex((jobEvent) => jobEvent.counter === 1);
  if (firstIndex && events[firstIndex]?.stdout) {
    const stdoutLines = events[firstIndex].stdout.split('\r\n');
    stdoutLines[0] = tracebackEvent.stdout;
    events[firstIndex].stdout = stdoutLines.join('\r\n');
  } else {
    countOffset += 1;
    events.unshift(tracebackEvent);
  }

  return {
    events,
    countOffset,
  };
}

export default function useJobEvents(job) {
  const [events, setEvents] = useState({});
  const [uuidMap, setUuidMap] = useState({});
  const [cssMap, setCssMap] = useState({});
  const [nodes, setNodes] = useState({});
  const [remoteRowCount, setRemoteRowCount] = useState(0);
  // TODO: track currentlyLoading?

  const addEvents = (newEvents, count) => {
    const { events: normalized, countOffset } = normalizeEvents(job, newEvents);

    const newResults = { ...events };
    const newUuidMap = { ...uuidMap };
    const newNodes = { ...nodes };
    let newResultsCssMap = {};
    normalized.forEach((jobEvent) => {
      const index = jobEvent.counter - 1;
      newResults[index] = jobEvent;
      newUuidMap[jobEvent.uuid] = index;
      if (jobEvent.parent_uuid && newUuidMap[jobEvent.parent_uuid]) {
        const parent = newResults[newUuidMap[jobEvent.parent_uuid]];
        // TODO: check for child events already loaded and set flag on this event
        if (!parent) {
          // TODO: trigger fetch of parent data?
          console.debug(`NO PARENT ${jobEvent.parent_uuid} FOR`, jobEvent);
        }
        if (parent) {
          parent.hasChildren = true;
        }
      }
      const { lineCssMap } = getLineTextHtml(jobEvent);
      newResultsCssMap = { ...newResultsCssMap, ...lineCssMap };
    });
    // TODO: update all as one state var in an update function setEvents(events => ...)
    setEvents({ ...newResults });
    setUuidMap(newUuidMap);
    if (count) {
      setRemoteRowCount(count + countOffset);
    }
    setCssMap(newResultsCssMap);
  };

  // TODO: replace while with recursive call
  const eventHasCollapsedParent = (event) => {
    if (!event) {
      return false;
    }
    let parentUuid = event.parent_uuid;
    while (parentUuid) {
      const parentEvent = events[uuidMap[parentUuid]];
      if (!parentEvent) {
        // TODO: trigger fetch of parent data?
        console.debug(`NO PARENT ${parentUuid} FOR`, event);
      }
      if (parentEvent && parentEvent.isCollapsed) {
        return true;
      }
      parentUuid = parentEvent?.parent_uuid;
    }
    return false;
  };

  // TODO: set isCollapsed on the tree node rather than event itself
  const toggleEventIsCollapsed = (index) => {
    const event = events[index];
    setEvents({
      ...events,
      [index]: {
        ...event,
        isCollapsed: !event.isCollapsed,
      },
    });
  };

  const getEventForRow = (rowIndex) => {
    //
  };

  return {
    events,
    remoteRowCount, // ?
    uuidMap, // ?
    cssMap,
    addEvents,
    setRemoteRowCount, // ? bring in any func using this?
    eventHasCollapsedParent,
    toggleEventIsCollapsed,
    getEventForRow,
  };
}
