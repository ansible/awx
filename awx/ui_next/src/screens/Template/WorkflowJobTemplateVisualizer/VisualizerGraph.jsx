import React, { Fragment, useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { calcZoomAndFit, constants, drawLinkLine, drawNodeTypeLetter, drawRootNode, enterLinks, enterNodes, getLinkOverlayPoints, layoutGraph, normalizeY } from '@util/workflow';
import { WorkflowHelp, WorkflowHelpDetails } from '@components/Workflow';

function Graph({ links, nodes, readOnly, i18n }) {
  const [helpText, setHelpText] = useState();
  const svgRef = useRef(null);
  const gRef = useRef(null);

  // This is the zoom function called by using the mousewheel/click and drag
  const zoom = () => {
    const translation = [d3.event.transform.x, d3.event.transform.y];
    d3.select(gRef.current).attr(
      'transform',
      `translate(${translation}) scale(${d3.event.transform.k})`
    );
  };

  const zoomRef = d3
    .zoom()
    .scaleExtent([0.1, 2])
    .on('zoom', zoom);

  // Initialize the zoom
  useEffect(() => {
    d3.select(svgRef.current).call(zoomRef);
  }, [zoomRef]);

  // Draw the graph - this will get triggered whenever
  // nodes or links changes
  useEffect(() => {
    const nodePositions = {};
    const svgGroup = d3.select(gRef.current);

    const g = layoutGraph(nodes, links);

    g.nodes().forEach(node => {
      nodePositions[node] = g.node(node);
    });

    const linkEnter = enterLinks(svgGroup, links);

    linkEnter
      .append('polygon', 'g')
      .attr('class', 'WorkflowGraph-linkOverlay')
      .attr('fill', '#E1E1E1')
      .style('opacity', '0')
      .attr('id', d => `link-${d.source.id}-${d.target.id}-overlay`)
      .attr('points', d => getLinkOverlayPoints(d, nodePositions))
      .on('mouseenter', d => {
        setHelpText(d);
      })
      .on('mouseleave', () => {
        setHelpText(null);
      });

    // Add entering links in the parent’s old position.
    drawLinkLine(linkEnter, nodePositions);

    linkEnter
      .append('polygon', 'g')
      .style('opacity', '0')
      .attr('points', d => getLinkOverlayPoints(d, nodePositions))
      .on('mouseenter', d => {
        setHelpText(d);
      })
      .on('mouseleave', () => {
        setHelpText(null);
      });

    linkEnter
      .on('mouseenter', d => {
        d3.select(`#link-${d.source.id}-${d.target.id}`).raise();
        d3.select(`#link-${d.source.id}-${d.target.id}-overlay`).style(
          'opacity',
          '1'
        );
        if (!readOnly) {
          d3
            .select(`#link-${d.source.id}-${d.target.id}`)
            .append('foreignObject')
            .attr('transform', () => {
              const normalizedSourceY = normalizeY(
                nodePositions,
                nodePositions[d.source.id].y
              );
              const halfSourceHeight = nodePositions[d.source.id].height / 2;
              const normalizedTargetY = normalizeY(
                nodePositions,
                nodePositions[d.target.id].y
              );
              const halfTargetHeight = nodePositions[d.target.id].height / 2;

              let yPos =
                (normalizedSourceY +
                  halfSourceHeight +
                  normalizedTargetY +
                  halfTargetHeight) /
                2;

              if (d.source.id === 1) {
                yPos += 4;
              }

              yPos -= 34;

              return `translate(${(nodePositions[d.source.id].x +
                nodePositions[d.source.id].width +
                nodePositions[d.target.id].x) /
                2}, ${yPos})`;
            })
            .attr('width', 52)
            .attr('height', 68)
            .attr('class', 'WorkflowGraph-tooltip').html(`
            <div class="WorkflowGraph-tooltipContents">
              <div class="WorkflowGraph-tooltipArrows">
                <div class="WorkflowGraph-tooltipArrows--outer"></div>
                <div class="WorkflowGraph-tooltipArrows--inner"></div>
              </div>
              <div class="WorkflowGraph-tooltipActions">
                <div id="node-add-between" class="WorkflowGraph-action WorkflowGraph-action--add">
                  <i class="pf-icon pf-icon-add-circle-o"></i>
                </div>
                <div id="link-edit" class="WorkflowGraph-action WorkflowGraph-action--edit">
                  <i class="pf-icon pf-icon-edit"></i>
                </div>
              </div>
            </div>
          `);

          d3.select('#node-add-between')
            .on('mouseenter', () => {
              setHelpText(i18n._(t`Add a new node between these two nodes`));
            })
            .on('mouseleave', () => {
              setHelpText(null);
            })
            .on('click', () => {});
          d3.select('#link-edit')
            .on('mouseenter', () => {
              setHelpText(i18n._(t`Edit this link`));
            })
            .on('mouseleave', () => {
              setHelpText(null);
            })
            .on('click', () => {});
        }
      })
      .on('mouseleave', d => {
        d3.select(`#link-${d.source.id}-${d.target.id}`).lower();
        d3.select(`#link-${d.source.id}-${d.target.id}-overlay`).style(
          'opacity',
          '0'
        );
        if (!readOnly) {
          linkEnter.select('.WorkflowGraph-tooltip').remove();
        }
      });

    const nodeEnter = enterNodes(svgGroup, nodes, nodePositions);

    nodeEnter.each((node, i, nodesArray) => {
      const nodeRef = d3.select(nodesArray[i]);
      if (node.id === 1) {
        drawRootNode(nodeRef);
        if (!readOnly) {
          nodeRef
            .on('mouseenter', () => {
              nodeRef
                .append('foreignObject')
                .attr('x', constants.rootW)
                .attr('y', 11)
                .attr('width', 52)
                .attr('height', 37)
                .attr('class', 'WorkflowGraph-tooltip').html(`
                <div class="WorkflowGraph-tooltipContents">
                  <div class="WorkflowGraph-tooltipArrows">
                    <div class="WorkflowGraph-tooltipArrows--outer"></div>
                    <div class="WorkflowGraph-tooltipArrows--inner"></div>
                  </div>
                  <div class="WorkflowGraph-tooltipActions">
                    <div id="node-add" class="WorkflowGraph-action WorkflowGraph-action--add">
                      <i class="pf-icon pf-icon-add-circle-o"></i>
                    </div>
                  </div>
                </div>
              `);
              d3.select('#node-add')
                .on('mouseenter', () => {
                  setHelpText(i18n._(t`Add a new node`));
                })
                .on('mouseleave', () => {
                  setHelpText(null);
                })
                .on('click', () => {});
            })
            .on('mouseleave', () => {
              nodeRef.select('.WorkflowGraph-tooltip').remove();
            });
        }
      } else {
        nodeRef
          .append('rect')
          .attr('width', constants.nodeW)
          .attr('height', constants.nodeH)
          .attr('rx', 2)
          .attr('ry', 2)
          .attr('stroke', '#93969A')
          .attr('stroke-width', '2px')
          .attr('fill', '#FFFFFF')
          .attr('class', d => {
            let classString = 'WorkflowGraph-rect';
            classString += !(d.unifiedJobTemplate && d.unifiedJobTemplate.name)
              ? ' WorkflowGraph-dashedNode'
              : '';
            return classString;
          });

        nodeRef
          .append('foreignObject')
          .attr('width', constants.nodeW)
          .attr('height', constants.nodeH)
          .attr('class', 'WorkflowGraph-nodeContents')
          .html(
            d =>
              `<p class="WorkflowGraph-nameText WorkflowGraph-ellipsisText">${
                d.unifiedJobTemplate
                  ? d.unifiedJobTemplate.name
                  : i18n._(t`DELETED`)
              }</p>`
          );

        nodeRef
          .append('rect')
          .attr('width', constants.nodeW)
          .attr('height', constants.nodeH)
          .style('opacity', '0')
          .on('mouseenter', d => {
            setHelpText(d);
          })
          .on('mouseleave', () => {
            setHelpText(null);
          });

        drawNodeTypeLetter(nodeRef);

        nodeRef
          .on('mouseenter', () => {
            nodeRef.select('.WorkflowGraph-rect').attr('stroke', '#007ABC');
            nodeRef.raise();
            if (readOnly) {
              nodeRef
                .append('foreignObject')
                .attr('x', constants.nodeW)
                .attr('y', 11)
                .attr('width', 52)
                .attr('height', 37)
                .attr('class', 'WorkflowGraph-tooltip').html(`
                    <div class="WorkflowGraph-tooltipContents">
                      <div class="WorkflowGraph-tooltipArrows">
                        <div class="WorkflowGraph-tooltipArrows--outer"></div>
                        <div class="WorkflowGraph-tooltipArrows--inner"></div>
                      </div>
                      <div class="WorkflowGraph-tooltipActions">
                        <div id="node-details" class="WorkflowGraph-action WorkflowGraph-action--details">
                          <i class="pf-icon pf-icon-info"></i>
                        </div>
                      </div>
                    </div>
                  `);
            } else {
              nodeRef
                .append('foreignObject')
                .attr('x', constants.nodeW)
                .attr('y', -49)
                .attr('width', 52)
                .attr('height', 157)
                .attr('class', 'WorkflowGraph-tooltip').html(`
                    <div class="WorkflowGraph-tooltipContents">
                      <div class="WorkflowGraph-tooltipArrows">
                        <div class="WorkflowGraph-tooltipArrows--outer"></div>
                        <div class="WorkflowGraph-tooltipArrows--inner"></div>
                      </div>
                      <div class="WorkflowGraph-tooltipActions">
                        <div id="node-add" class="WorkflowGraph-action WorkflowGraph-action--add">
                          <i class="pf-icon pf-icon-add-circle-o"></i>
                        </div>
                        <div id="node-details" class="WorkflowGraph-action WorkflowGraph-action--details">
                          <i class="pf-icon pf-icon-info"></i>
                        </div>
                        <div id="node-edit" class="WorkflowGraph-action WorkflowGraph-action--edit">
                          <i class="pf-icon pf-icon-edit"></i>
                        </div>
                        <div id="node-link" class="WorkflowGraph-action WorkflowGraph-action--link">
                          <i class="pf-icon pf-icon-automation"></i>
                        </div>
                        <div id="node-delete" class="WorkflowGraph-action WorkflowGraph-action--delete">
                          <i class="pf-icon pf-icon-remove2"></i>
                        </div>
                      </div>
                    </div>
                  `);
              d3.select('#node-add')
                .on('mouseenter', () => {
                  setHelpText(i18n._(t`Add a new node`));
                })
                .on('mouseleave', () => {
                  setHelpText(null);
                })
                .on('click', () => {});
              d3.select('#node-edit')
                .on('mouseenter', () => {
                  setHelpText(i18n._(t`Edit this node`));
                })
                .on('mouseleave', () => {
                  setHelpText(null);
                })
                .on('click', () => {});
              d3.select('#node-link')
                .on('mouseenter', () => {
                  setHelpText(i18n._(t`Link to an available node`));
                })
                .on('mouseleave', () => {
                  setHelpText(null);
                })
                .on('click', () => {});
              d3.select('#node-delete')
                .on('mouseenter', () => {
                  setHelpText(i18n._(t`Remove this node`));
                })
                .on('mouseleave', () => {
                  setHelpText(null);
                })
                .on('click', () => {});
            }

            d3.select('#node-details')
              .on('mouseenter', () => {
                setHelpText(i18n._(t`View node details`));
              })
              .on('mouseleave', () => {
                setHelpText(null);
              })
              .on('click', () => {});
          })
          .on('mouseleave', () => {
            nodeRef.select('.WorkflowGraph-rect').attr('stroke', '#93969A');
            nodeRef.select('.WorkflowGraph-tooltip').remove();
          });
      }
    });

    // This will make sure that all the link elements appear before the nodes in the dom
    svgGroup.selectAll('.WorkflowGraph-node').order();
  }, [links, nodes, readOnly, i18n]);

  // Attempt to zoom the graph to fit the available screen space
  useEffect(() => {
    const gBoundingClientRect = d3
      .select(gRef.current)
      .node()
      .getBoundingClientRect();

    const gBBoxDimensions = d3
      .select(gRef.current)
      .node()
      .getBBox();

    // For some reason the root width needs to be added?
    gBoundingClientRect.width += constants.rootW;

    const svgElement = document.getElementById("workflow-svg");
    const svgBoundingClientRect = svgElement.getBoundingClientRect();

    const [scaleToFit, yTranslate] = calcZoomAndFit(svgBoundingClientRect, gBoundingClientRect, gBBoxDimensions);

    d3.select(svgRef.current).call(
      zoomRef.transform,
      d3.zoomIdentity
        .translate(0, yTranslate)
        .scale(scaleToFit)
    );
    // We only want this to run once (when the component mounts)
    // but this rule will throw a warning if we don't include
    // things like height, width, currentScale in the array
    // of deps.  Including them will cause this hook to fire
    // as those deps change.
    // Discussion: https://github.com/facebook/create-react-app/issues/6880
    // and https://github.com/facebook/react/issues/15865 amongst others
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Fragment>
      {helpText && helpText !== '' && (
        <WorkflowHelp>
          {typeof helpText === 'string' && <Fragment>{helpText}</Fragment>}
          {typeof helpText === 'object' && <WorkflowHelpDetails d={helpText} />}
        </WorkflowHelp>
      )}
      <svg id="workflow-svg" ref={svgRef}>
        <g id="workflow-g" ref={gRef} />
      </svg>
    </Fragment>
  );
}

export default withI18n()(Graph);
