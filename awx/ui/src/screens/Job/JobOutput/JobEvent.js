import React, { useEffect } from 'react';
import {
  JobEventLine,
  JobEventLineToggle,
  JobEventLineNumber,
  JobEventLineText,
} from './shared';

function JobEvent({
  style,
  lineTextHtml,
  isClickable,
  onJobEventClick,
  event,
  measure,
  isVisible,
  onToggleExpanded,
}) {
  useEffect(() => {
    measure();
  }, [event.isCollapsed, isVisible, measure]);

  if (!isVisible) {
    return null;
  }
  return !event.stdout ? null : (
    <div style={style} type={event.type}>
      {lineTextHtml.map(
        ({ lineNumber, html }) =>
          lineNumber >= 0 && (
            <JobEventLine
              onClick={isClickable ? onJobEventClick : undefined}
              key={`${event.counter}-${lineNumber}`}
              isFirst={lineNumber === 0}
              isClickable={isClickable}
            >
              <JobEventLineToggle />
              {event.hasChildren && html.length ? (
                <button onClick={onToggleExpanded} type="button">
                  {event.isCollapsed ? '+' : '-'}
                </button>
              ) : (
                ' '
              )}
              <JobEventLineNumber>
                {lineNumber}
                {event.isCollapsed && html.length ? (
                  <>
                    <br />
                    ...
                  </>
                ) : null}
              </JobEventLineNumber>
              <JobEventLineText
                type="job_event_line_text"
                dangerouslySetInnerHTML={{
                  __html: html,
                }}
              />
            </JobEventLine>
          )
      )}
    </div>
  );
}

export default JobEvent;
