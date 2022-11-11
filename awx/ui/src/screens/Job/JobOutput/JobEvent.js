import React, { useEffect } from 'react';
import {
  JobEventLine,
  JobEventLineToggle,
  JobEventLineNumber,
  JobEventLineText,
  JobEventEllipsis,
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
  jobStatus,
}) {
  const numOutputLines = lineTextHtml?.length || 0;
  useEffect(() => {
    const timeout = setTimeout(measure, 0);
    return () => {
      clearTimeout(timeout);
    };
  }, [numOutputLines, isCollapsed, measure, jobStatus]);

  let toggleLineIndex = -1;
  if (hasChildren) {
    lineTextHtml.forEach(({ html }, index) => {
      if (html) {
        toggleLineIndex = index;
      }
    });
  }
  return !event.stdout ? null : (
    <div style={style} type={event.type}>
      {lineTextHtml.map(({ lineNumber, html }, index) => {
        if (lineNumber < 0) {
          return null;
        }
        const canToggle = index === toggleLineIndex && !event.isTracebackOnly;
        return (
          <JobEventLine
            onClick={isClickable ? onJobEventClick : undefined}
            key={`${event.counter}-${lineNumber}`}
            isFirst={lineNumber === 0}
            isClickable={isClickable}
          >
            <JobEventLineToggle
              canToggle={canToggle}
              isCollapsed={isCollapsed}
              onToggle={onToggleCollapsed}
            />
            <JobEventLineNumber>
              {!event.isTracebackOnly ? lineNumber : ''}
              <JobEventEllipsis isCollapsed={isCollapsed && canToggle} />
            </JobEventLineNumber>
            <JobEventLineText
              type="job_event_line_text"
              dangerouslySetInnerHTML={{
                __html: html,
              }}
            />
          </JobEventLine>
        );
      })}
    </div>
  );
}

export default JobEvent;
