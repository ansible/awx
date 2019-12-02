import React, { Fragment, useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import * as dagre from 'dagre';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import WorkflowHelp from './WorkflowHelp';
import WorkflowHelpDetails from './WorkflowHelpDetails';

const SVG = styled.svg`
  display: flex;
  height: 100%;
  background-color: #f6f6f6;

  .WorkflowChart-tooltip {
    padding-left: 5px;
  }

  .WorkflowChart-action {
    height: 25px;
    width: 25px;
    font-size: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    border-radius: 2px;
  }

  .WorkflowChart-action:hover {
    color: white;
  }

  .WorkflowChart-action:not(:last-of-type) {
    margin-bottom: 5px;
  }

  .WorkflowChart-action--add:hover {
    background-color: #58b957;
  }

  .WorkflowChart-action--edit:hover,
  .WorkflowChart-action--link:hover,
  .WorkflowChart-action--details:hover {
    background-color: #0279bc;
  }

  .WorkflowChart-action--delete:hover {
    background-color: #d9534f;
  }

  .WorkflowChart-tooltipArrows {
    width: 10px;
  }

  .WorkflowChart-tooltipArrows--outer {
    position: absolute;
    top: calc(50% - 10px);
    width: 0;
    height: 0;
    border-right: 10px solid #c4c4c4;
    border-top: 10px solid transparent;
    border-bottom: 10px solid transparent;
    margin: auto;
  }

  .WorkflowChart-tooltipArrows--inner {
    position: absolute;
    top: calc(50% - 10px);
    left: 6px;
    width: 0;
    height: 0;
    border-right: 10px solid white;
    border-top: 10px solid transparent;
    border-bottom: 10px solid transparent;
    margin: auto;
  }

  .WorkflowChart-tooltipActions {
    background-color: white;
    border: 1px solid #c4c4c4;
    border-radius: 2px;
    padding: 5px;
  }

  .WorkflowChart-tooltipContents {
    display: flex;
  }

  .WorkflowChart-nameText {
    font-size: 13px;
    padding: 0px 10px;
    text-align: center;
    p {
      margin-top: 20px;
      white-space: nowrap;
      text-overflow: ellipsis;
      overflow: hidden;
    }
  }
`;

function Graph({ links, nodes, readOnly, i18n }) {
  const [helpText, setHelpText] = useState();
  const svgRef = useRef(null);
  const gRef = useRef(null);
  const nodeW = 180;
  const nodeH = 60;
  // This needs to be dynamic bc the text can be different lengths in different languages
  const rootW = 72;
  const rootH = 40;
  let currentScale = 1;

  // Dagre is going to shift the root node around as nodes are added/removed
  // This function ensures that the user doesn't experience that
  const normalizeY = (nodePositions, y) => {
    return y - nodePositions[1].y;
  };

  // This is the zoom function called by using the mousewheel/click and drag
  const zoom = () => {
    const translation = [d3.event.transform.x, d3.event.transform.y];
    d3.select(gRef.current).attr(
      'transform',
      `translate(${translation}) scale(${d3.event.transform.k})`
    );
    currentScale = d3.event.transform.k;
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
    const line = d3
      .line()
      .x(d => {
        return d.x;
      })
      .y(d => {
        return d.y;
      });
    const getLinkOverlayPoints = d => {
      const sourceX =
        nodePositions[d.source.id].x + nodePositions[d.source.id].width + 1;
      let sourceY =
        normalizeY(nodePositions, nodePositions[d.source.id].y) +
        nodePositions[d.source.id].height / 2;
      const targetX = nodePositions[d.target.id].x - 1;
      const targetY =
        normalizeY(nodePositions, nodePositions[d.target.id].y) +
        nodePositions[d.target.id].height / 2;

      // There's something off with the math on the root node...
      if (d.source.id === 1) {
        sourceY += 10;
      }
      const slope = (targetY - sourceY) / (targetX - sourceX);
      const yIntercept = targetY - slope * targetX;
      const orthogonalDistance = 8;

      const pt1 = [
        targetX,
        slope * targetX +
          yIntercept +
          orthogonalDistance * Math.sqrt(1 + slope * slope),
      ].join(',');
      const pt2 = [
        sourceX,
        slope * sourceX +
          yIntercept +
          orthogonalDistance * Math.sqrt(1 + slope * slope),
      ].join(',');
      const pt3 = [
        sourceX,
        slope * sourceX +
          yIntercept -
          orthogonalDistance * Math.sqrt(1 + slope * slope),
      ].join(',');
      const pt4 = [
        targetX,
        slope * targetX +
          yIntercept -
          orthogonalDistance * Math.sqrt(1 + slope * slope),
      ].join(',');

      return [pt1, pt2, pt3, pt4].join(' ');
    };
    const lineData = d => {
      const sourceX =
        nodePositions[d.source.id].x + nodePositions[d.source.id].width + 1;
      let sourceY =
        normalizeY(nodePositions, nodePositions[d.source.id].y) +
        nodePositions[d.source.id].height / 2;
      const targetX = nodePositions[d.target.id].x - 1;
      const targetY =
        normalizeY(nodePositions, nodePositions[d.target.id].y) +
        nodePositions[d.target.id].height / 2;

      // There's something off with the math on the root node...
      if (d.source.id === 1) {
        sourceY += 10;
      }

      return line([
        {
          x: sourceX,
          y: sourceY,
        },
        {
          x: targetX,
          y: targetY,
        },
      ]);
    };
    const svgGroup = d3.select(gRef.current);

    const g = new dagre.graphlib.Graph();

    g.setGraph({ rankdir: 'LR', nodesep: 30, ranksep: 120 });

    // This is needed for Dagre
    g.setDefaultEdgeLabel(() => {
      return {};
    });

    nodes.forEach(node => {
      if (node.id === 1) {
        g.setNode(node.id, { label: '', width: rootW, height: rootH });
      } else {
        g.setNode(node.id, { label: '', width: nodeW, height: nodeH });
      }
    });

    links.forEach(link => {
      g.setEdge(link.source.id, link.target.id);
    });

    dagre.layout(g);

    g.nodes().forEach(node => {
      nodePositions[node] = g.node(node);
    });

    const linkRefs = svgGroup
      .selectAll('.WorkflowChart-link')
      .data(links, d => {
        return `${d.source.id}-${d.target.id}`;
      });

    // Remove any stale links
    linkRefs.exit().remove();

    // Add any new links
    const linkEnter = linkRefs
      .enter()
      .append('g')
      .attr('class', 'WorkflowChart-link')
      .attr('id', d => `link-${d.source.id}-${d.target.id}`)
      .attr('stroke-width', '2px');

    linkEnter
      .append('polygon', 'g')
      .attr('class', 'WorkflowChart-linkOverlay')
      .attr('fill', '#E1E1E1')
      .style('opacity', '0')
      .attr('id', d => `link-${d.source.id}-${d.target.id}-overlay`)
      .attr('points', d => getLinkOverlayPoints(d))
      .on('mouseenter', d => {
        setHelpText(d);
      })
      .on('mouseleave', () => {
        setHelpText(null);
      });

    // Add entering links in the parent’s old position.
    linkEnter
      .insert('path', 'g')
      .attr('class', 'WorkflowChart-linkPath')
      .attr('d', d => lineData(d))
      .attr('stroke', d => {
        if (d.edgeType) {
          if (d.edgeType === 'failure') {
            return '#d9534f';
          }
          if (d.edgeType === 'success') {
            return '#5cb85c';
          }
          if (d.edgeType === 'always') {
            return '#337ab7';
          }
        }
        return '#D7D7D7';
      });

    linkEnter
      .append('polygon', 'g')
      .style('opacity', '0')
      .attr('points', d => getLinkOverlayPoints(d))
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
            .attr('class', 'WorkflowChart-tooltip').html(`
            <div class="WorkflowChart-tooltipContents">
              <div class="WorkflowChart-tooltipArrows">
                <div class="WorkflowChart-tooltipArrows--outer"></div>
                <div class="WorkflowChart-tooltipArrows--inner"></div>
              </div>
              <div class="WorkflowChart-tooltipActions">
                <div id="node-add-between" class="WorkflowChart-action WorkflowChart-action--add">
                  <i class="pf-icon pf-icon-add-circle-o"></i>
                </div>
                <div id="link-edit" class="WorkflowChart-action WorkflowChart-action--edit">
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
          linkEnter.select('.WorkflowChart-tooltip').remove();
        }
      });

    const nodeRefs = svgGroup
      .selectAll('.WorkflowChart-node')
      .data(nodes, d => {
        return d.id;
      });

    // Remove any stale nodes
    nodeRefs.exit().remove();

    // Add new nodes
    const nodeEnter = nodeRefs
      .enter()
      .append('g')
      .attr('class', 'WorkflowChart-node')
      .attr('id', d => `node-${d.id}`)
      .attr(
        'transform',
        d =>
          `translate(${nodePositions[d.id].x},${normalizeY(
            nodePositions,
            nodePositions[d.id].y
          )})`
      );

    nodeEnter.each((node, i, nodesArray) => {
      const nodeRef = d3.select(nodesArray[i]);
      if (node.id === 1) {
        nodeRef
          .append('rect')
          .attr('width', rootW)
          .attr('height', rootH)
          .attr('y', 10)
          .attr('rx', 2)
          .attr('ry', 2)
          .attr('fill', '#0279BC')
          .attr('class', 'WorkflowChart-rootNode');
        nodeRef
          .append('text')
          .attr('x', 13)
          .attr('y', 30)
          .attr('dy', '.35em')
          .attr('fill', 'white')
          .attr('class', 'WorkflowChart-startText')
          .text('START');

        if (!readOnly) {
          nodeRef
            .on('mouseenter', () => {
              nodeRef
                .append('foreignObject')
                .attr('x', rootW)
                .attr('y', 11)
                .attr('width', 52)
                .attr('height', 37)
                .attr('class', 'WorkflowChart-tooltip').html(`
                <div class="WorkflowChart-tooltipContents">
                  <div class="WorkflowChart-tooltipArrows">
                    <div class="WorkflowChart-tooltipArrows--outer"></div>
                    <div class="WorkflowChart-tooltipArrows--inner"></div>
                  </div>
                  <div class="WorkflowChart-tooltipActions">
                    <div id="node-add" class="WorkflowChart-action WorkflowChart-action--add">
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
              nodeRef.select('.WorkflowChart-tooltip').remove();
            });
        }
      } else {
        nodeRef
          .append('rect')
          .attr('width', nodeW)
          .attr('height', nodeH)
          .attr('rx', 2)
          .attr('ry', 2)
          .attr('stroke', '#93969A')
          .attr('stroke-width', '2px')
          .attr('fill', '#FFFFFF')
          .attr('class', d => {
            let classString = 'WorkflowChart-rect';
            classString += !(d.unifiedJobTemplate && d.unifiedJobTemplate.name)
              ? ' WorkflowChart-dashedNode'
              : '';
            return classString;
          });

        nodeRef
          .append('foreignObject')
          .attr('width', nodeW)
          .attr('height', nodeH)
          .attr('class', 'WorkflowChart-nameText')
          .html(
            d =>
              `<p>${
                d.unifiedJobTemplate
                  ? d.unifiedJobTemplate.name
                  : i18n._(t`DELETED`)
              }</p>`
          );

        nodeRef
          .append('rect')
          .attr('width', nodeW)
          .attr('height', nodeH)
          .style('opacity', '0')
          .on('mouseenter', d => {
            setHelpText(d);
          })
          .on('mouseleave', () => {
            setHelpText(null);
          });

        nodeRef
          .append('circle')
          .attr('cy', nodeH)
          .attr('r', 10)
          .attr('class', 'WorkflowChart-nodeTypeCircle')
          .attr('fill', '#393F43')
          .style('display', d => (d.unifiedJobTemplate ? null : 'none'));

        nodeRef
          .append('text')
          .attr('y', nodeH)
          .attr('dy', '.35em')
          .attr('text-anchor', 'middle')
          .attr('fill', '#FFFFFF')
          .attr('class', 'WorkflowChart-nodeTypeLetter')
          .text(d => {
            let nodeTypeLetter;
            if (d.unifiedJobTemplate && d.unifiedJobTemplate.type) {
              switch (d.unifiedJobTemplate.type) {
                case 'job_template':
                  nodeTypeLetter = 'JT';
                  break;
                case 'project':
                  nodeTypeLetter = 'P';
                  break;
                case 'inventory_source':
                  nodeTypeLetter = 'I';
                  break;
                case 'workflow_job_template':
                  nodeTypeLetter = 'W';
                  break;
                default:
                  nodeTypeLetter = '';
              }
            } else if (
              d.unifiedJobTemplate &&
              d.unifiedJobTemplate.unified_job_type
            ) {
              switch (d.unifiedJobTemplate.unified_job_type) {
                case 'job':
                  nodeTypeLetter = 'JT';
                  break;
                case 'project_update':
                  nodeTypeLetter = 'P';
                  break;
                case 'inventory_update':
                  nodeTypeLetter = 'I';
                  break;
                case 'workflow_job':
                  nodeTypeLetter = 'W';
                  break;
                default:
                  nodeTypeLetter = '';
              }
            }
            return nodeTypeLetter;
          })
          .style('font-size', '10px')
          .style('display', d => {
            return d.unifiedJobTemplate &&
              d.unifiedJobTemplate.type !== 'workflow_approval_template' &&
              d.unifiedJobTemplate.unified_job_type !== 'workflow_approval'
              ? null
              : 'none';
          });

        nodeRef
          .on('mouseenter', () => {
            nodeRef.select('.WorkflowChart-rect').attr('stroke', '#007ABC');
            nodeRef.raise();
            if (readOnly) {
              nodeRef
                .append('foreignObject')
                .attr('x', nodeW)
                .attr('y', 11)
                .attr('width', 52)
                .attr('height', 37)
                .attr('class', 'WorkflowChart-tooltip').html(`
                    <div class="WorkflowChart-tooltipContents">
                      <div class="WorkflowChart-tooltipArrows">
                        <div class="WorkflowChart-tooltipArrows--outer"></div>
                        <div class="WorkflowChart-tooltipArrows--inner"></div>
                      </div>
                      <div class="WorkflowChart-tooltipActions">
                        <div id="node-details" class="WorkflowChart-action WorkflowChart-action--details">
                          <i class="pf-icon pf-icon-info"></i>
                        </div>
                      </div>
                    </div>
                  `);
            } else {
              nodeRef
                .append('foreignObject')
                .attr('x', nodeW)
                .attr('y', -49)
                .attr('width', 52)
                .attr('height', 157)
                .attr('class', 'WorkflowChart-tooltip').html(`
                    <div class="WorkflowChart-tooltipContents">
                      <div class="WorkflowChart-tooltipArrows">
                        <div class="WorkflowChart-tooltipArrows--outer"></div>
                        <div class="WorkflowChart-tooltipArrows--inner"></div>
                      </div>
                      <div class="WorkflowChart-tooltipActions">
                        <div id="node-add" class="WorkflowChart-action WorkflowChart-action--add">
                          <i class="pf-icon pf-icon-add-circle-o"></i>
                        </div>
                        <div id="node-details" class="WorkflowChart-action WorkflowChart-action--details">
                          <i class="pf-icon pf-icon-info"></i>
                        </div>
                        <div id="node-edit" class="WorkflowChart-action WorkflowChart-action--edit">
                          <i class="pf-icon pf-icon-edit"></i>
                        </div>
                        <div id="node-link" class="WorkflowChart-action WorkflowChart-action--link">
                          <i class="pf-icon pf-icon-automation"></i>
                        </div>
                        <div id="node-delete" class="WorkflowChart-action WorkflowChart-action--delete">
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
            nodeRef.select('.WorkflowChart-rect').attr('stroke', '#93969A');
            nodeRef.select('.WorkflowChart-tooltip').remove();
          });
      }
    });

    // This will make sure that all the link elements appear before the nodes in the dom
    svgGroup.selectAll('.WorkflowChart-node').order();
  }, [links, nodes, readOnly, i18n]);

  // Attempt to zoom the graph to fit the available screen space
  useEffect(() => {
    // TODO: try to figure out this start node width thing...
    const startNodeWidth = 60;
    const gDimensions = d3
      .select(gRef.current)
      .node()
      .getBoundingClientRect();

    const pageHeight = window.innerHeight - 50;
    const pageWidth = window.innerWidth;

    // For some reason the start node isn't accounted for in the width... add it
    gDimensions.width += startNodeWidth * currentScale;

    const scaleNeededForMaxHeight =
      pageHeight / (gDimensions.height / currentScale);
    const scaleNeededForMaxWidth =
      pageWidth / (gDimensions.width / currentScale);
    const lowerScale = Math.min(
      scaleNeededForMaxHeight,
      scaleNeededForMaxWidth
    );

    let scaleToFit;
    if (lowerScale < 0.5 || lowerScale > 2) {
      scaleToFit = lowerScale;
    } else {
      scaleToFit = Math.floor(lowerScale * 1000) / 1000;
    }

    d3.select(svgRef.current).call(
      zoomRef.transform,
      d3.zoomIdentity
        .translate(0, pageHeight / 2 - (nodeH * scaleToFit) / 2)
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
      <SVG id="workflow-svg" ref={svgRef}>
        <g id="workflow-g" ref={gRef} />
      </SVG>
    </Fragment>
  );
}

export default withI18n()(Graph);
