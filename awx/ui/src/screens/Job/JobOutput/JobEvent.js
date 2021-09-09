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
  isCollapsed,
  onToggleCollapsed,
  hasChildren,
}) {
  useEffect(() => {
    measure();
  }, [event, isCollapsed, measure]);

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
              {hasChildren && html.length ? (
                <button onClick={onToggleCollapsed} type="button">
                  {isCollapsed ? '+' : '-'}
                </button>
              ) : (
                ' '
              )}
              <JobEventLineNumber>
                {lineNumber}
                {isCollapsed && html.length ? (
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
