/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['moment', '$timeout', '$window', '$filter', 'TemplatesStrings',
    function(moment, $timeout, $window, $filter, TemplatesStrings) {

    return {
        scope: {
            graphState: '=',
            readOnly: '<',
            addNodeWithoutChild: '&',
            addNodeWithChild: '&',
            editNode: '&',
            deleteNode: '&',
            editLink: '&',
            selectNodeForLinking: '&',
            workflowZoomed: '&',
            mode: '@'
        },
        restrict: 'E',
        link: function(scope, element) {

            // Quickly render the start text so we see how wide it is and know how wide to make the start
            // node element.
            const startNodeText = $(`<span class="WorkflowChart-node" style="visibility:hidden;"><span class="WorkflowChart-startText">${TemplatesStrings.get('workflow_maker.START')}</span></span>`);
            startNodeText.appendTo(document.body);
            const startNodeTextWidth = startNodeText.width();
            startNodeText.remove();

            let nodeW = 180,
                nodeH = 60,
                rootW = startNodeTextWidth + 25,
                rootH = 40,
                strokeW = 2, // px
                startNodeOffsetY = scope.mode === 'details' ? 17 : 10,
                maxNodeTextLength = 27,
                windowHeight,
                windowWidth,
                line,
                zoomObj,
                baseSvg,
                svgGroup,
                graphLoaded,
                nodePositionMap = {};

            scope.dimensionsSet = false;

            const calcAvailableScreenSpace = () => {
                let dimensions = {};

                if(scope.mode !== 'details') {
                    // This is the workflow editor
                    dimensions.height = $('.WorkflowMaker-contentLeft').outerHeight() - $('.WorkflowLegend-maker').outerHeight();
                    dimensions.width = $('#workflow-modal-dialog').width() - $('.WorkflowMaker-contentRight').outerWidth();
                }
                else {
                    // This is the workflow details view
                    let panel = $('.WorkflowResults-rightSide').children('.card')[0];
                    let panelWidth = $(panel).width();
                    let panelHeight = $(panel).height();
                    let headerHeight = $('.StandardOut-panelHeader').outerHeight();
                    let legendHeight = $('.WorkflowLegend-details').outerHeight();
                    let proposedHeight = panelHeight - headerHeight - legendHeight - 40;

                    dimensions.height = proposedHeight > 200 ? proposedHeight : 200;
                    dimensions.width = panelWidth;
                }

                return dimensions;
            };

            // Dagre is going to shift the root node around as nodes are added/removed
            // This function ensures that the user doesn't experience that
            const normalizeY = ((y) => {
                return y - nodePositionMap[1].y;
            });

            const lineData = (d) => {

                let sourceX = nodePositionMap[d.source.id].x + (nodePositionMap[d.source.id].width);
                let sourceY = normalizeY(nodePositionMap[d.source.id].y) + (nodePositionMap[d.source.id].height/2);
                let targetX = nodePositionMap[d.target.id].x;
                let targetY = normalizeY(nodePositionMap[d.target.id].y) + (nodePositionMap[d.target.id].height/2);

                // There's something off with the math on the root node...
                if (d.source.id === 1) {
                    if (scope.mode === "details") {
                        sourceY = sourceY + 17;
                    } else {
                        sourceY = sourceY + 10;
                    }
                }

                let points = [{
                        x: sourceX,
                        y: sourceY
                    },
                    {
                        x: targetX,
                        y: targetY
                    }
                ];

                return line(points);
            };

            // TODO: this function is hacky and we need to come up with a better solution
            // see: http://stackoverflow.com/questions/15975440/add-ellipses-to-overflowing-text-in-svg#answer-27723752
            const wrap = (text) => {
                if(text) {
                    return text.length > maxNodeTextLength ? text.substring(0,maxNodeTextLength) + '...' : text;
                }
                else {
                    return '';
                }
            };

            const rounded_rect = (x, y, w, h, r, tl, tr, bl, br) => {
                // x, y - position coordinates
                // w - width
                // h - height
                // r - border radius
                // round the top-left corner (bool)
                // round the top-right corner (bool)
                // round the bottom-left corner (bool)
                // round the bottom-right corner (bool)
                let retval;
                retval  = "M" + (x + r) + "," + y;
                retval += "h" + (w - 2*r);
                if (tr) { retval += "a" + r + "," + r + " 0 0 1 " + r + "," + r; }
                else { retval += "h" + r; retval += "v" + r; }
                retval += "v" + (h - 2*r);
                if (br) { retval += "a" + r + "," + r + " 0 0 1 " + -r + "," + r; }
                else { retval += "v" + r; retval += "h" + -r; }
                retval += "h" + (2*r - w);
                if (bl) { retval += "a" + r + "," + r + " 0 0 1 " + -r + "," + -r; }
                else { retval += "h" + -r; retval += "v" + -r; }
                retval += "v" + (2*r - h);
                if (tl) { retval += "a" + r + "," + r + " 0 0 1 " + r + "," + -r; }
                else { retval += "v" + -r; retval += "h" + r; }
                retval += "z";
                return retval;
            };

            // This is the zoom function called by using the mousewheel/click and drag
            const naturalZoom = () => {
                let scale = d3.event.scale,
                    translation = d3.event.translate;

                translation = [translation[0], translation[1] + ((windowHeight/2 - rootH/2 - startNodeOffsetY)*scale)];

                svgGroup.attr("transform", `translate(${translation})scale(${scale})`);

                scope.workflowZoomed({
                    zoom: scale
                });
            };

            // This is the zoom that gets called when the user interacts with the manual zoom controls
            const manualZoom = (zoom) => {
                let scale = zoom / 100,
                translation = zoomObj.translate(),
                origZoom = zoomObj.scale(),
                unscaledOffsetX = (translation[0] + ((windowWidth*origZoom) - windowWidth)/2)/origZoom,
                unscaledOffsetY = (translation[1] + ((windowHeight*origZoom) - windowHeight)/2)/origZoom,
                translateX = unscaledOffsetX*scale - ((scale*windowWidth)-windowWidth)/2,
                translateY = unscaledOffsetY*scale - ((scale*windowHeight)-windowHeight)/2;

                svgGroup.attr("transform", `translate(${[translateX, translateY + ((windowHeight/2 - rootH/2 - startNodeOffsetY)*scale)]})scale(${scale})`);
                zoomObj.scale(scale);
                zoomObj.translate([translateX, translateY]);
            };

            const manualPan = (direction) => {
                let scale = zoomObj.scale(),
                    distance = 150 * scale,
                    translateX,
                    translateY,
                    translateCoords = zoomObj.translate();
                if (direction === 'left' || direction === 'right') {
                    translateX = direction === 'left' ? translateCoords[0] - distance : translateCoords[0] + distance;
                    translateY = translateCoords[1];
                } else if (direction === 'up' || direction === 'down') {
                    translateX = translateCoords[0];
                    translateY = direction === 'up' ? translateCoords[1] - distance : translateCoords[1] + distance;
                }
                svgGroup.attr("transform", `translate(${translateX},${(translateY + ((windowHeight/2 - rootH/2 - startNodeOffsetY)*scale))})scale(${scale})`);
                zoomObj.translate([translateX, translateY]);
            };

            const resetZoomAndPan = () => {
                svgGroup.attr("transform", `translate(0,${(windowHeight/2 - rootH/2 - startNodeOffsetY)})scale(1)`);
                // Update the zoomObj
                zoomObj.scale(1);
                zoomObj.translate([0,0]);
            };

            const zoomToFitChart = () => {
                const startNodeWidth = scope.mode === 'details' ? 25 : 60,
                graphDimensions = d3.select('#aw-workflow-chart-g')[0][0].getBoundingClientRect(),
                availableScreenSpace = calcAvailableScreenSpace(),
                currentZoomValue = zoomObj.scale();

                // For some reason the start node isn't accounted for in the width... add it
                graphDimensions.width = graphDimensions.width + (startNodeWidth*currentZoomValue);

                const unscaledH = graphDimensions.height/currentZoomValue,
                unscaledW = graphDimensions.width/currentZoomValue,
                scaleNeededForMaxHeight = (availableScreenSpace.height)/unscaledH,
                scaleNeededForMaxWidth = (availableScreenSpace.width)/unscaledW,
                lowerScale = Math.min(scaleNeededForMaxHeight, scaleNeededForMaxWidth),
                scaleToFit = lowerScale < 0.5 ? 0.5 : (lowerScale > 2 ? 2 : Math.floor(lowerScale * 1000)/1000);

                manualZoom(scaleToFit*100);

                scope.workflowZoomed({
                    zoom: scaleToFit
                });

                svgGroup.attr("transform", `translate(0, ${(windowHeight/2 - (nodeH*scaleToFit/2))})scale(${scaleToFit})`);
                zoomObj.translate([0, windowHeight/2 - (nodeH*scaleToFit/2) - ((windowHeight/2 - rootH/2 - startNodeOffsetY)*scaleToFit)]);
            };

            const buildLinkTooltip = (d) => {
                let edgeTypeLabel;
                switch(d.edgeType) {
                    case "always":
                        edgeTypeLabel = TemplatesStrings.get('workflow_maker.ALWAYS');
                        break;
                    case "success":
                        edgeTypeLabel = TemplatesStrings.get('workflow_maker.ON_SUCCESS');
                        break;
                    case "failure":
                        edgeTypeLabel = TemplatesStrings.get('workflow_maker.ON_FAILURE');
                        break;
                }
                let linkInstructionText = !scope.readOnly ? TemplatesStrings.get('workflow_maker.EDIT_LINK_TOOLTIP') : TemplatesStrings.get('workflow_maker.VIEW_LINK_TOOLTIP');
                let linkTooltip = svgGroup.append("g")
                    .attr("class", "WorkflowChart-tooltip");
                const tipRef = linkTooltip.append("foreignObject")
                    // In order for this to work in FF a height of at least 1 must be present
                    .attr("width", 100)
                    .attr("height", 1)
                    .style("overflow", "visible")
                    .html(`
                        <div class='WorkflowChart-tooltipContents'>
                            <div>${TemplatesStrings.get('workflow_maker.RUN')}: ${edgeTypeLabel}</div>
                            <div>${linkInstructionText}</div>
                        </div>
                    `);
                const tipDimensions = tipRef.select('.WorkflowChart-tooltipContents').node().getBoundingClientRect();
                let sourceNode = d3.select(`#node-${d.source.id}`);
                const sourceNodeX = d3.transform(sourceNode.attr("transform")).translate[0];
                const sourceNodeY = d3.transform(sourceNode.attr("transform")).translate[1];
                let targetNode = d3.select(`#node-${d.target.id}`);
                const targetNodeX = d3.transform(targetNode.attr("transform")).translate[0];
                const targetNodeY = d3.transform(targetNode.attr("transform")).translate[1];
                let xPos, yPos, arrowPoints;
                const scaledHeight = tipDimensions.height/zoomObj.scale();

                if (nodePositionMap[d.source.id].y === nodePositionMap[d.target.id].y) {
                    xPos = (sourceNodeX + nodeW + targetNodeX)/2 - 50;
                    yPos = sourceNodeY + nodeH/2 - scaledHeight - 20;
                     arrowPoints = {
                        pt1: {
                            x: xPos + 40,
                            y: yPos + scaledHeight
                        },
                        pt2: {
                            x: xPos + 60,
                            y: yPos + scaledHeight
                        },
                        pt3: {
                            x: xPos + 50,
                            y: yPos + scaledHeight + 10
                        }
                    };
                } else {
                    xPos = (sourceNodeX + nodeW + targetNodeX)/2 - 120;
                    yPos = (sourceNodeY + (nodeH/2) + targetNodeY + (nodeH/2))/2 - (scaledHeight/2);
                     arrowPoints = {
                        pt1: {
                            x: xPos + 100,
                            y: yPos + (scaledHeight/2) - 10
                        },
                        pt2: {
                            x: xPos + 100,
                            y: yPos + (scaledHeight/2) + 10
                        },
                        pt3: {
                            x: xPos + 110,
                            y: yPos + (scaledHeight/2)
                        }
                    };
                }

                linkTooltip.append("polygon")
                    .attr("class", "WorkflowChart-tooltipArrow")
                    .attr("points", `${arrowPoints.pt1.x},${arrowPoints.pt1.y} ${arrowPoints.pt2.x},${arrowPoints.pt2.y} ${arrowPoints.pt3.x},${arrowPoints.pt3.y}`);

                tipRef.attr('height', scaledHeight);
                tipRef.attr("transform", `translate(${xPos},${yPos})`);
            };

            const updateGraph = () => {
                if(scope.dimensionsSet) {
                    let g = new dagre.graphlib.Graph();

                    g.setGraph({rankdir: 'LR', nodesep: 30, ranksep: 120});

                    // This is needed for Dagre
                    g.setDefaultEdgeLabel(() => { return {}; });

                    scope.graphState.arrayOfNodesForChart.forEach((node) => {
                        if (node.id === 1) {
                            if (scope.mode === "details") {
                                g.setNode(node.id, { label: "",  width: 25, height: 25 });
                            } else {
                                g.setNode(node.id, { label: "",  width: rootW, height: rootH });
                            }
                        } else {
                            g.setNode(node.id, { label: "",  width: nodeW, height: nodeH });
                        }
                    });

                    scope.graphState.arrayOfLinksForChart.forEach((link) => {
                        g.setEdge(link.source.id, link.target.id);
                    });

                    dagre.layout(g);

                    nodePositionMap = {};

                    g.nodes().forEach((node) => {
                        nodePositionMap[node] = g.node(node);
                    });

                    let links = svgGroup.selectAll(".WorkflowChart-link")
                        .data(scope.graphState.arrayOfLinksForChart, (d) => { return `${d.source.id}-${d.target.id}`; });

                    // Remove any stale links
                    links.exit().remove();

                    // Update existing links
                    baseSvg.selectAll(".WorkflowChart-link")
                        .attr("id", (d) => `link-${d.source.id}-${d.target.id}`);

                    baseSvg.selectAll(".WorkflowChart-linkPath")
                        .transition()
                        .attr("d", lineData)
                        .attr('stroke', (d) => {
                            let edgeType = d.edgeType;
                            if(edgeType) {
                                if(edgeType === "failure") {
                                    return "#d9534f";
                                } else if(edgeType === "success") {
                                    return "#5cb85c";
                                } else if(edgeType === "always"){
                                    return "#337ab7";
                                } else if (edgeType === "placeholder") {
                                    return "#B9B9B9";
                                }
                            }
                            else {
                                return "#D7D7D7";
                            }
                        });

                    baseSvg.selectAll(".WorkflowChart-linkOverlay")
                        .attr("id", (d) => `link-${d.source.id}-${d.target.id}-overlay`)
                        .attr("class", (d) => {
                            let linkClasses = ["WorkflowChart-linkOverlay"];
                            if (
                                scope.graphState.linkBeingEdited &&
                                d.source.id === scope.graphState.linkBeingEdited.source &&
                                d.target.id === scope.graphState.linkBeingEdited.target
                            ) {
                                linkClasses.push("WorkflowChart-link--active");
                            }
                            return linkClasses.join(' ');
                        })
                        .attr("points",(d) => {
                            let x1 = nodePositionMap[d.target.id].x;
                            let y1 = normalizeY(nodePositionMap[d.target.id].y) + (nodePositionMap[d.target.id].height/2);
                            let x2 = nodePositionMap[d.source.id].x + nodePositionMap[d.target.id].width;
                            let y2 = normalizeY(nodePositionMap[d.source.id].y) + (nodePositionMap[d.source.id].height/2);
                            let slope = (y2 - y1)/(x2-x1);
                            let yIntercept = y1 - slope*x1;
                            let orthogonalDistance = 8;

                            const pt1 = [x1, slope*x1 + yIntercept + orthogonalDistance*Math.sqrt(1+slope*slope)].join(",");
                            const pt2 = [x2, slope*x2 + yIntercept + orthogonalDistance*Math.sqrt(1+slope*slope)].join(",");
                            const pt3 = [x2, slope*x2 + yIntercept - orthogonalDistance*Math.sqrt(1+slope*slope)].join(",");
                            const pt4 = [x1, slope*x1 + yIntercept - orthogonalDistance*Math.sqrt(1+slope*slope)].join(",");

                            return [pt1, pt2, pt3, pt4].join(" ");
                        });

                    baseSvg.selectAll(".WorkflowChart-circleBetweenNodes")
                        .attr("id", (d) => `link-${d.source.id}-${d.target.id}-add`)
                        .style("display", (d) => { return (d.edgeType === 'placeholder' || scope.graphState.isLinkMode || d.source.id === scope.graphState.nodeBeingAdded || d.target.id === scope.graphState.nodeBeingAdded || scope.readOnly) ? "none" : null; })
                        .attr("cx", (d) => {
                            return (nodePositionMap[d.source.id].x + nodePositionMap[d.source.id].width + nodePositionMap[d.target.id].x)/2;
                        })
                        .attr("cy", (d) => {
                            const normalizedSourceY = normalizeY(nodePositionMap[d.source.id].y);
                            const halfSourceHeight = nodePositionMap[d.source.id].height/2;
                            const normalizedTargetY = normalizeY(nodePositionMap[d.target.id].y);
                            const halfTargetHeight = nodePositionMap[d.target.id].height/2;

                            let yPos = (normalizedSourceY + halfSourceHeight + normalizedTargetY + halfTargetHeight)/2;

                            if (d.source.id === 1) {
                                yPos = yPos + 4;
                            }

                            return yPos;
                        });

                    baseSvg.selectAll(".WorkflowChart-betweenNodesIcon")
                        .style("display", (d) => { return (d.edgeType === 'placeholder' || scope.graphState.isLinkMode || d.source.id === scope.graphState.nodeBeingAdded || d.target.id === scope.graphState.nodeBeingAdded || scope.readOnly) ? "none" : null; })
                        .attr("transform", (d) => {
                            let translate;

                            const normalizedSourceY = normalizeY(nodePositionMap[d.source.id].y);
                            const halfSourceHeight = nodePositionMap[d.source.id].height/2;
                            const normalizedTargetY = normalizeY(nodePositionMap[d.target.id].y);
                            const halfTargetHeight = nodePositionMap[d.target.id].height/2;

                            let yPos = (normalizedSourceY + halfSourceHeight + normalizedTargetY + halfTargetHeight)/2;

                            if (d.source.id === 1) {
                                yPos = yPos + 4;
                            }

                            translate = `translate(${(nodePositionMap[d.source.id].x + nodePositionMap[d.source.id].width + nodePositionMap[d.target.id].x)/2}, ${yPos})`;
                            return translate;
                        });

                    // Add any new links
                    let linkEnter = links.enter().append("g")
                       .attr("class", "WorkflowChart-link")
                       .attr("id", (d) => `link-${d.source.id}-${d.target.id}`);

                     linkEnter.append("polygon", "g")
                          .attr("class", (d) => {
                              let linkClasses = ["WorkflowChart-linkOverlay"];
                              if (
                                  scope.graphState.linkBeingEdited &&
                                  d.source.id === scope.graphState.linkBeingEdited.source &&
                                  d.target.id === scope.graphState.linkBeingEdited.target
                              ) {
                                  linkClasses.push("WorkflowChart-link--active");
                              }
                              return linkClasses.join(' ');
                          })
                          .attr("id", (d) => `link-${d.source.id}-${d.target.id}-overlay`)
                          .call(edit_link)
                          .attr("points",(d) => {
                              let x1 = nodePositionMap[d.target.id].x;
                              let y1 = normalizeY(nodePositionMap[d.target.id].y) + (nodePositionMap[d.target.id].height/2);
                              let x2 = nodePositionMap[d.source.id].x + nodePositionMap[d.target.id].width;
                              let y2 = normalizeY(nodePositionMap[d.source.id].y) + (nodePositionMap[d.source.id].height/2);
                              let slope = (y2 - y1)/(x2-x1);
                              let yIntercept = y1 - slope*x1;
                              let orthogonalDistance = 8;

                              const pt1 = [x1, slope*x1 + yIntercept + orthogonalDistance*Math.sqrt(1+slope*slope)].join(",");
                              const pt2 = [x2, slope*x2 + yIntercept + orthogonalDistance*Math.sqrt(1+slope*slope)].join(",");
                              const pt3 = [x2, slope*x2 + yIntercept - orthogonalDistance*Math.sqrt(1+slope*slope)].join(",");
                              const pt4 = [x1, slope*x1 + yIntercept - orthogonalDistance*Math.sqrt(1+slope*slope)].join(",");

                              return [pt1, pt2, pt3, pt4].join(" ");
                          })
                          .on("mouseover", (d) => {
                              if(
                                  d.edgeType !== 'placeholder' &&
                                  !scope.graphState.isLinkMode &&
                                  d.source.id !== 1 &&
                                  d.source.id !== scope.graphState.nodeBeingAdded &&
                                  d.target.id !== scope.graphState.nodeBeingAdded &&
                                  scope.mode !== 'details'
                              ) {
                                  $(`#link-${d.source.id}-${d.target.id}`).appendTo(`#aw-workflow-chart-g`);
                                  d3.select(`#link-${d.source.id}-${d.target.id}`)
                                      .classed("WorkflowChart-linkHovering", true);

                                  buildLinkTooltip(d);
                              }
                          })
                          .on("mouseout", (d) => {
                              if(d.source.id !== 1 && d.target.id !== scope.graphState.nodeBeingAdded && scope.mode !== 'details') {
                                  $(`#aw-workflow-chart-g`).prepend($(`#link-${d.source.id}-${d.target.id}`));
                                  d3.select(`#link-${d.source.id}-${d.target.id}`)
                                      .classed("WorkflowChart-linkHovering", false);
                              }
                              $('.WorkflowChart-tooltip').remove();
                          });

                    // Add entering links in the parent’s old position.
                    linkEnter.insert("path", "g")
                         .attr("class", "WorkflowChart-linkPath")
                         .attr("d", lineData)
                         .call(edit_link)
                         .on("mouseenter", (d) => {
                             if(
                                 d.edgeType !== 'placeholder' &&
                                 !scope.graphState.isLinkMode &&
                                 d.source.id !== 1 &&
                                 d.source.id !== scope.graphState.nodeBeingAdded &&
                                 d.target.id !== scope.graphState.nodeBeingAdded &&
                                 scope.mode !== 'details'
                             ) {
                                 $(`#link-${d.source.id}-${d.target.id}`).appendTo(`#aw-workflow-chart-g`);
                                 d3.select(`#link-${d.source.id}-${d.target.id}`)
                                     .classed("WorkflowChart-linkHovering", true);

                                 buildLinkTooltip(d);
                             }
                         })
                         .on("mouseleave", (d) => {
                             if(d.source.id !== 1 && d.target.id !== scope.graphState.nodeBeingAdded && scope.mode !== 'details') {
                                 $(`#aw-workflow-chart-g`).prepend($(`#link-${d.source.id}-${d.target.id}`));
                                 d3.select(`#link-${d.source.id}-${d.target.id}`)
                                     .classed("WorkflowChart-linkHovering", false);
                             }
                             $('.WorkflowChart-tooltip').remove();
                         })
                         .attr('stroke', (d) => {
                             let edgeType = d.edgeType;
                             if(d.edgeType) {
                                 if(edgeType === "failure") {
                                     return "#d9534f";
                                 } else if(edgeType === "success") {
                                     return "#5cb85c";
                                 } else if(edgeType === "always"){
                                     return "#337ab7";
                                 } else if (edgeType === "placeholder") {
                                     return "#B9B9B9";
                                 }
                             }
                             else {
                                 return "#D7D7D7";
                             }
                         });

                     linkEnter.append("circle")
                          .attr("id", (d) => `link-${d.source.id}-${d.target.id}-add`)
                          .attr("r", 10)
                          .attr("class", "WorkflowChart-addCircle WorkflowChart-circleBetweenNodes")
                          .style("display", (d) => { return (d.edgeType === 'placeholder' || scope.graphState.isLinkMode || d.source.id === scope.graphState.nodeBeingAdded || d.target.id === scope.graphState.nodeBeingAdded || scope.readOnly) ? "none" : null; })
                          .attr("cx", (d) => {
                              return (nodePositionMap[d.source.id].x + nodePositionMap[d.source.id].width + nodePositionMap[d.target.id].x)/2;
                          })
                          .attr("cy", (d) => {
                              const normalizedSourceY = normalizeY(nodePositionMap[d.source.id].y);
                              const halfSourceHeight = nodePositionMap[d.source.id].height/2;
                              const normalizedTargetY = normalizeY(nodePositionMap[d.target.id].y);
                              const halfTargetHeight = nodePositionMap[d.target.id].height/2;

                              let yPos = (normalizedSourceY + halfSourceHeight + normalizedTargetY + halfTargetHeight)/2;

                              if (d.source.id === 1) {
                                  yPos = yPos + 4;
                              }

                              return yPos;
                          })
                          .call(add_node_with_child)
                          .on("mouseover", (d) => {
                              $(`#link-${d.source.id}-${d.target.id}`).appendTo(`#aw-workflow-chart-g`);
                              d3.select(`#link-${d.source.id}-${d.target.id}`)
                                  .classed("WorkflowChart-addHovering", true);
                          })
                          .on("mouseout", (d) => {
                              $(`#aw-workflow-chart-g`).prepend($(`#link-${d.source.id}-${d.target.id}`));
                              d3.select(`#link-${d.source.id}-${d.target.id}`)
                                  .classed("WorkflowChart-addHovering", false);
                          });

                     linkEnter.append("path")
                          .attr("class", "WorkflowChart-betweenNodesIcon")
                          .style("fill", "white")
                          .attr("d", d3.svg.symbol()
                              .size(60)
                              .type("cross")
                          )
                          .style("display", (d) => { return (d.edgeType === 'placeholder' || scope.graphState.isLinkMode || d.source.id === scope.graphState.nodeBeingAdded || d.target.id === scope.graphState.nodeBeingAdded || scope.readOnly) ? "none" : null; })
                          .attr("transform", (d) => {
                              const normalizedSourceY = normalizeY(nodePositionMap[d.source.id].y);
                              const halfSourceHeight = nodePositionMap[d.source.id].height/2;
                              const normalizedTargetY = normalizeY(nodePositionMap[d.target.id].y);
                              const halfTargetHeight = nodePositionMap[d.target.id].height/2;

                              let yPos = (normalizedSourceY + halfSourceHeight + normalizedTargetY + halfTargetHeight)/2;

                              if (d.source.id === 1) {
                                  yPos = yPos + 4;
                              }

                              return `translate(${(nodePositionMap[d.source.id].x + nodePositionMap[d.source.id].width + nodePositionMap[d.target.id].x)/2}, ${yPos})`;
                          })
                          .call(add_node_with_child)
                          .on("mouseover", (d) => {
                              $(`#link-${d.source.id}-${d.target.id}`).appendTo(`#aw-workflow-chart-g`);
                              d3.select(`#link-${d.source.id}-${d.target.id}`)
                                  .classed("WorkflowChart-addHovering", true);
                          })
                          .on("mouseout", (d) => {
                              $(`#aw-workflow-chart-g`).prepend($(`#link-${d.source.id}-${d.target.id}`));
                              d3.select(`#link-${d.source.id}-${d.target.id}`)
                                  .classed("WorkflowChart-addHovering", false);
                          });

                    let nodes = svgGroup.selectAll('.WorkflowChart-node')
                        .data(scope.graphState.arrayOfNodesForChart, (d) => { return d.id; });

                    // Remove any stale nodes
                    nodes.exit().remove();

                    // Update existing nodes
                    baseSvg.selectAll(".WorkflowChart-node")
                        .transition()
                        .attr("transform", (d) => {
                            // Update prior x and prior y
                            d.px = d.x;
                            d.py = d.y;
                            return `translate(${nodePositionMap[d.id].x}, ${normalizeY(nodePositionMap[d.id].y)})`;
                    });

                    baseSvg.selectAll(".WorkflowChart-nodeAddCircle")
                        .style("display", (d) => { return scope.graphState.isLinkMode || d.id === scope.graphState.nodeBeingAdded || scope.readOnly ? "none" : null; });

                    baseSvg.selectAll(".WorkflowChart-nodeAddIcon")
                        .style("display", (d) => { return scope.graphState.isLinkMode || d.id === scope.graphState.nodeBeingAdded || scope.readOnly ? "none" : null; });

                    baseSvg.selectAll(".WorkflowChart-linkCircle")
                        .style("display", (d) => { return scope.graphState.isLinkMode || d.id === scope.graphState.nodeBeingAdded || scope.readOnly ? "none" : null; });

                    baseSvg.selectAll(".WorkflowChart-nodeLinkIcon")
                        .style("display", (d) => { return scope.graphState.isLinkMode || d.id === scope.graphState.nodeBeingAdded || scope.readOnly ? "none" : null; });

                    baseSvg.selectAll(".WorkflowChart-nodeRemoveCircle")
                        .style("display", (d) => { return scope.graphState.isLinkMode || d.id === scope.graphState.nodeBeingAdded || scope.readOnly ? "none" : null; });

                    baseSvg.selectAll(".WorkflowChart-nodeRemoveIcon")
                        .style("display", (d) => { return scope.graphState.isLinkMode || d.id === scope.graphState.nodeBeingAdded || scope.readOnly ? "none" : null; });

                    baseSvg.selectAll(".WorkflowChart-rect")
                        .attr('stroke', (d) => {
                            if(d.job && d.job.status) {
                                if(d.job.status === "successful"){
                                    return "#5cb85c";
                                }
                                else if (d.job.status === "failed" || d.job.status === "error" || d.job.status === "canceled") {
                                    return "#d9534f";
                                }
                                else {
                                    return "#D7D7D7";
                                }
                            }
                            else {
                                return "#D7D7D7";
                            }
                         })
                         .attr("class", (d) => {
                             let classString = d.id === scope.graphState.nodeBeingAdded ? "WorkflowChart-rect WorkflowChart-isNodeBeingAdded" : "WorkflowChart-rect";
                             classString += !d.unifiedJobTemplate ? " WorkflowChart-dashedNode" : "";
                             return classString;
                         });

                    baseSvg.selectAll(".WorkflowChart-nodeOverlay")
                        .attr("class", (d) => { return d.isInvalidLinkTarget ? "WorkflowChart-nodeOverlay WorkflowChart-nodeOverlay--disabled" : "WorkflowChart-nodeOverlay WorkflowChart-nodeOverlay--transparent"; });

                    baseSvg.selectAll(".WorkflowChart-nodeTypeCircle")
                    .style("display", (d) => d.unifiedJobTemplate ? null : "none");

                    baseSvg.selectAll(".WorkflowChart-nodeTypeLetter")
                        .text((d) => {
                            let nodeTypeLetter = "";
                            if (d.unifiedJobTemplate && d.unifiedJobTemplate.type) {
                                switch (d.unifiedJobTemplate.type) {
                                    case "job_template":
                                        nodeTypeLetter = "JT";
                                        break;
                                    case "project":
                                        nodeTypeLetter = "P";
                                        break;
                                    case "inventory_source":
                                        nodeTypeLetter = "I";
                                        break;
                                    case "workflow_job_template":
                                        nodeTypeLetter = "W";
                                        break;
                                }
                            } else if (d.unifiedJobTemplate && d.unifiedJobTemplate.unified_job_type) {
                                switch (d.unifiedJobTemplate.unified_job_type) {
                                    case "job":
                                        nodeTypeLetter = "JT";
                                        break;
                                    case "project_update":
                                        nodeTypeLetter = "P";
                                        break;
                                    case "inventory_update":
                                        nodeTypeLetter = "I";
                                        break;
                                    case "workflow_job":
                                        nodeTypeLetter = "W";
                                        break;
                                }
                            }
                            return nodeTypeLetter;
                        })
                        .style("display", (d) => {
                            return d.unifiedJobTemplate &&
                            d.unifiedJobTemplate.type !== "workflow_approval_template" &&
                            d.unifiedJobTemplate.unified_job_type !== "workflow_approval" ? null : "none";
                        });

                        baseSvg.selectAll(".WorkflowChart-nodeTypeLetter")
                        .text((d) => {
                            let nodeTypeLetter = "";
                            if (d.unifiedJobTemplate && d.unifiedJobTemplate.type) {
                                switch (d.unifiedJobTemplate.type) {
                                    case "job_template":
                                        nodeTypeLetter = "JT";
                                        break;
                                    case "project":
                                        nodeTypeLetter = "P";
                                        break;
                                    case "inventory_source":
                                        nodeTypeLetter = "I";
                                        break;
                                    case "workflow_job_template":
                                        nodeTypeLetter = "W";
                                        break;
                                }
                            } else if (d.unifiedJobTemplate && d.unifiedJobTemplate.unified_job_type) {
                                switch (d.unifiedJobTemplate.unified_job_type) {
                                    case "job":
                                        nodeTypeLetter = "JT";
                                        break;
                                    case "project_update":
                                        nodeTypeLetter = "P";
                                        break;
                                    case "inventory_update":
                                        nodeTypeLetter = "I";
                                        break;
                                    case "workflow_job":
                                        nodeTypeLetter = "W";
                                        break;
                                }
                            }
                            return nodeTypeLetter;
                        })
                        .style("display", (d) => {
                            return d.unifiedJobTemplate &&
                            d.unifiedJobTemplate.type !== "workflow_approval_template" &&
                            d.unifiedJobTemplate.unified_job_type !== "workflow_approval" ? null : "none";
                        });

                    baseSvg.selectAll(".WorkflowChart-pauseIcon")
                    .style("display", (d) => {
                        return d.unifiedJobTemplate &&
                        (d.unifiedJobTemplate.type === "workflow_approval_template" ||
                        d.unifiedJobTemplate.unified_job_type === "workflow_approval") ? null : "none";
                    });

                    baseSvg.selectAll(".WorkflowChart-nodeStatus")
                        .attr("class", (d) => {
                            let statusClasses = ["WorkflowChart-nodeStatus"];

                            if(d.job){
                                switch(d.job.status) {
                                    case "pending":
                                    case "waiting":
                                    case "running":
                                        statusClasses.push("WorkflowChart-nodeStatus--running");
                                        break;
                                    case "successful":
                                        statusClasses.push("WorkflowChart-nodeStatus--success");
                                        break;
                                    case "failed":
                                    case "error":
                                        statusClasses.push("WorkflowChart-nodeStatus--failed");
                                        break;
                                    case "canceled":
                                        statusClasses.push("WorkflowChart-nodeStatus--canceled");
                                        break;
                                }
                            }

                            return statusClasses.join(' ');
                        })
                        .style("display", (d) => { return d.job && d.job.status ? null : "none"; })
                        .transition()
                        .duration(0)
                        .attr("r", 6)
                        .each(function(d) {
                            if(d.job && d.job.status && (d.job.status === "pending" || d.job.status === "waiting" || d.job.status === "running")) {
                                // Pulse the circle
                                let circle = d3.select(this);
                                (function repeat() {
                                    circle = circle.transition()
                                        .duration(2000)
                                        .attr("r", 6)
                                        .transition()
                                        .duration(2000)
                                        .attr("r", 0)
                                        .ease('sine')
                                        .each("end", repeat);
                                })();
                            }
                        });

                    baseSvg.selectAll(".WorkflowChart-nameText")
                        .attr("x", function(d){ return (scope.mode === 'details' && d.job && d.job.status) ? 20 : nodeW / 2; })
                        .attr("y", function(d){ return (scope.mode === 'details' && d.job && d.job.status) ? 10 : nodeH / 2; })
                        .attr("text-anchor", function(d){ return (scope.mode === 'details' && d.job && d.job.status) ? "inherit" : "middle"; })
                        .text((d) => wrap(_.get(d, 'unifiedJobTemplate.name')));

                    baseSvg.selectAll(".WorkflowChart-detailsLink")
                        .style("display", (d) => {
                            const isApprovalStep = d.unifiedJobTemplate && d.unifiedJobTemplate.unified_job_type === 'workflow_approval';
                            return d.job &&
                                !isApprovalStep &&
                                d.job.status &&
                                d.job.id ? null : "none";
                        })
                        .html((d) => {
                            let href = "";
                            if (d.job) {
                                href = `/#/workflow_node_results/${d.job.id}`;
                            }
                            return `<a href="${href}">${TemplatesStrings.get('workflow_maker.DETAILS')}</a>`;
                        });

                    baseSvg.selectAll(".WorkflowChart-deletedText")
                        .attr("y", (d) => { return scope.mode === 'details' && d.job && d.job.type === "workflow_approval" && (d.job.timed_out || d.job.status === "failed" || d.job.status === "successful") ? 29 : 22; })
                        .style("display", (d) => { return d.unifiedJobTemplate || d.id === scope.graphState.nodeBeingAdded ? "none" : null; });

                    baseSvg.selectAll(".WorkflowChart-timedOutText")
                        .attr("y", (d) => { return scope.mode === 'details' && !d.unifiedJobTemplate ? 15 : 22; })
                        .style("display", (d) => { return d.job && d.job.timed_out ? null : "none"; });

                    baseSvg.selectAll(".WorkflowChart-deniedText")
                        .attr("y", (d) => { return scope.mode === 'details' && !d.unifiedJobTemplate ? 15 : 22; })
                        .style("display", (d) => { return d.job && d.job.type === "workflow_approval" && d.job.status === "failed" && !d.job.timed_out ? null : "none"; });

                    baseSvg.selectAll(".WorkflowChart-approvedText")
                        .attr("y", (d) => { return scope.mode === 'details' && !d.unifiedJobTemplate ? 15 : 22; })
                        .style("display", (d) => { return d.job && d.job.type === "workflow_approval" && d.job.status === "successful" && !d.job.timed_out ? null : "none"; });

                    baseSvg.selectAll(".WorkflowChart-activeNode")
                        .style("display", (d) => { return d.id === scope.graphState.nodeBeingEdited ? null : "none"; });

                    baseSvg.selectAll(".WorkflowChart-elapsed")
                        .style("display", (d) => { return (d.job && d.job.elapsed) ? null : "none"; });

                    baseSvg.selectAll(".WorkflowChart-addLinkCircle")
                        .attr("fill", (d) => { return scope.graphState.addLinkSource === d.id ? "#337AB7" : "#D7D7D7"; })
                        .style("display", (d) => { return scope.graphState.isLinkMode && !d.isInvalidLinkTarget ? null : "none"; });

                    baseSvg.selectAll(".WorkflowChart-convergenceTypeRectangle")
                        .style("display", (d) => d.all_parents_must_converge ? null : "none");

                    // Add new nodes
                    const nodeEnter = nodes
                      .enter()
                      .append('g')
                      .attr("class", "WorkflowChart-node")
                      .attr("id", (d) => `node-${d.id}`)
                      .attr("transform", (d) => `translate(${nodePositionMap[d.id].x},${normalizeY(nodePositionMap[d.id].y)})`);

                    nodeEnter.each(function(d) {
                        let thisNode = d3.select(this);
                        if(d.id === 1 && scope.mode === 'details') {
                            // Overwrite the default root height and width and replace it with a small blue square
                            rootW = 25;
                            rootH = 25;
                            thisNode.append("rect")
                                .attr("width", rootW)
                                .attr("height", rootH)
                                .attr("y", startNodeOffsetY)
                                .attr("rx", 5)
                                .attr("ry", 5)
                                .attr("fill", "#337ab7")
                                .attr("class", "WorkflowChart-rootNode");
                        }
                        else if(d.id === 1 && scope.mode !== 'details') {
                            thisNode.append("rect")
                                .attr("width", rootW)
                                .attr("height", rootH)
                                .attr("y", 10)
                                .attr("rx", 5)
                                .attr("ry", 5)
                                .attr("fill", "#5cb85c")
                                .attr("class", "WorkflowChart-rootNode")
                                .call(add_node_without_child);
                            thisNode.append("text")
                                .attr("x", 13)
                                .attr("y", 30)
                                .attr("dy", ".35em")
                                .attr("class", "WorkflowChart-startText")
                                .text(TemplatesStrings.get('workflow_maker.START'))
                                .call(add_node_without_child);
                        }
                        else {
                            thisNode.append("circle")
                                .attr("cy", nodeH/2)
                                .attr("cx", nodeW)
                                .attr("r", 8)
                                .attr("class", "WorkflowChart-addLinkCircle")
                                .style("display", scope.graphState.isLinkMode ? null : "none");
                            thisNode.append("rect")
                                .attr("width", nodeW)
                                .attr("height", nodeH)
                                .attr("rx", 5)
                                .attr("ry", 5)
                                .attr('stroke', (d) => {
                                    if(d.job && d.job.status) {
                                        if(d.job.status === "successful"){
                                            return "#5cb85c";
                                        }
                                        else if (d.job.status === "failed" || d.job.status === "error" || d.job.status === "canceled") {
                                            return "#d9534f";
                                        }
                                        else {
                                            return "#D7D7D7";
                                        }
                                    }
                                    else {
                                        return "#D7D7D7";
                                    }
                                })
                                .attr('stroke-width', `${strokeW}px`)
                                .attr("class", (d) => {
                                    let classString = d.id === scope.graphState.nodeBeingAdded ? "WorkflowChart-rect WorkflowChart-isNodeBeingAdded" : "WorkflowChart-rect";
                                    classString += !_.get(d, 'unifiedJobTemplate.name') ? " WorkflowChart-dashedNode" : "";
                                    return classString;
                                });

                            thisNode.append("path")
                                .attr("d", rounded_rect(1, 0, 5, nodeH, 5, 1, 0, 1, 0))
                                .attr("class", "WorkflowChart-activeNode")
                                .style("display", (d) => { return d.id === scope.graphState.nodeBeingEdited ? null : "none"; });

                            thisNode.append("text")
                                .attr("x", function(d){ return (scope.mode === 'details' && d.job && d.job.status) ? 20 : nodeW / 2; })
                                .attr("y", function(d){ return (scope.mode === 'details' && d.job && d.job.status) ? 10 : nodeH / 2; })
                                .attr("dy", ".35em")
                                .attr("text-anchor", function(d){ return (scope.mode === 'details' && d.job && d.job.status) ? "inherit" : "middle"; })
                                .attr("class", "WorkflowChart-defaultText WorkflowChart-nameText")
                                .text((d) => wrap(_.get(d, 'unifiedJobTemplate.name')));

                            thisNode.append("foreignObject")
                                .attr("x", 0)
                                .attr("y", (d) => { return scope.mode === 'details' && d.job && d.job.type === "workflow_approval" && (d.job.timed_out || d.job.status === "failed" || d.job.status === "successful") ? 29 : 22; })
                                .attr("dy", ".35em")
                                .attr("text-anchor", "middle")
                                .attr("class", "WorkflowChart-defaultText WorkflowChart-deletedText")
                                .html(`<span>${TemplatesStrings.get('workflow_maker.DELETED')}</span>`)
                                .style("display", (d) => { return d.unifiedJobTemplate || d.id === scope.graphState.nodeBeingAdded ? "none" : null; });

                            thisNode.append("foreignObject")
                                .attr("x", 0)
                                .attr("y", (d) => { return scope.mode === 'details' && !d.unifiedJobTemplate ? 15 : 22; })
                                .attr("dy", ".35em")
                                .attr("text-anchor", "middle")
                                .attr("class", "WorkflowChart-defaultText WorkflowChart-timedOutText")
                                .html(`<span>${TemplatesStrings.get('workflow_maker.TIMED_OUT')}</span>`)
                                .style("display", (d) => { return d.job && d.job.type === "workflow_approval" && d.job.timed_out ? null : "none"; });

                            thisNode.append("foreignObject")
                                .attr("x", 0)
                                .attr("y", (d) => { return scope.mode === 'details' && !d.unifiedJobTemplate ? 15 : 22; })
                                .attr("dy", ".35em")
                                .attr("text-anchor", "middle")
                                .attr("class", "WorkflowChart-defaultText WorkflowChart-deniedText")
                                .html(`<span>${TemplatesStrings.get('workflow_maker.DENIED')}</span>`)
                                .style("display", (d) => { return d.job && d.job.type === "workflow_approval" && d.job.status === "failed" && !d.job.timed_out ? null : "none"; });

                            thisNode.append("foreignObject")
                                .attr("x", 0)
                                .attr("y", (d) => { return scope.mode === 'details' && !d.unifiedJobTemplate ? 15 : 22; })
                                .attr("dy", ".35em")
                                .attr("text-anchor", "middle")
                                .attr("class", "WorkflowChart-defaultText WorkflowChart-approvedText")
                                .html(`<span>${TemplatesStrings.get('workflow_maker.APPROVED')}</span>`)
                                .style("display", (d) => { return d.job && d.job.type === "workflow_approval" && d.job.status === "successful" && !d.job.timed_out ? null : "none"; });

                            // Build the 'ALL' symbol for all-convergence nodes
                            const convergenceTypeHeight = nodeH / 5;
                            const convergenceTypeWidth = nodeW / 5;
                            const convergenceTypeXCoord = nodeW / 2 - convergenceTypeWidth / 2;
                            const convergenceTypeYCoord = -convergenceTypeHeight + (strokeW / 2);
                            const convergenceTypeBorderRadius = 3;

                            const convergenceRectangle = rounded_rect(
                                convergenceTypeXCoord,
                                convergenceTypeYCoord,
                                convergenceTypeWidth,
                                convergenceTypeHeight,
                                convergenceTypeBorderRadius,
                                true,  // round top-left
                                true,  // round top-right
                                false, // round bottom-left
                                false  // round bottom-right
                            );
                            thisNode.append("path")
                                .attr("d", convergenceRectangle)
                                .attr("class", "WorkflowChart-convergenceTypeRectangle")
                                .style("display", (d) => d.all_parents_must_converge ? null : "none");
                            thisNode.append("text")
                                .attr("y", ((convergenceTypeYCoord + convergenceTypeHeight) / 2) - Math.min(strokeW, 2))
                                .attr("x", convergenceTypeXCoord + (convergenceTypeWidth / 4))
                                .attr("class", "WorkflowChart-convergenceTypeLetter")
                                .text("ALL");

                            thisNode.append("circle")
                                .attr("cy", nodeH)
                                .attr("r", 10)
                                .attr("class", "WorkflowChart-nodeTypeCircle")
                                .style("display", (d) => d.unifiedJobTemplate ? null : "none");

                            thisNode.append("text")
	                            .attr("y", nodeH)
	                            .attr("dy", ".35em")
	                            .attr("text-anchor", "middle")
	                            .attr("class", "WorkflowChart-nodeTypeLetter")
	                            .text((d) => {
                                    let nodeTypeLetter = "";
                                    if (d.unifiedJobTemplate && d.unifiedJobTemplate.type) {
                                        switch (d.unifiedJobTemplate.type) {
                                            case "job_template":
                                                nodeTypeLetter = "JT";
                                                break;
                                            case "project":
                                                nodeTypeLetter = "P";
                                                break;
                                            case "inventory_source":
                                                nodeTypeLetter = "I";
                                                break;
                                            case "workflow_job_template":
                                                nodeTypeLetter = "W";
                                                break;
                                        }
                                    } else if (d.unifiedJobTemplate && d.unifiedJobTemplate.unified_job_type) {
                                        switch (d.unifiedJobTemplate.unified_job_type) {
                                            case "job":
                                                nodeTypeLetter = "JT";
                                                break;
                                            case "project_update":
                                                nodeTypeLetter = "P";
                                                break;
                                            case "inventory_update":
                                                nodeTypeLetter = "I";
                                                break;
                                            case "workflow_job":
                                                nodeTypeLetter = "W";
                                                break;
                                        }
                                    }
                                    return nodeTypeLetter;
                                })
	                            .style("display", (d) => {
	                                return d.unifiedJobTemplate &&
	                                (d.unifiedJobTemplate.type === "project" ||
                                    d.unifiedJobTemplate.unified_job_type === "project_update" ||
                                    d.unifiedJobTemplate.type === "job_template" ||
                                    d.unifiedJobTemplate.unified_job_type === "job" ||
	                                d.unifiedJobTemplate.type === "inventory_source" ||
	                                d.unifiedJobTemplate.unified_job_type === "inventory_update" ||
	                                d.unifiedJobTemplate.type === "workflow_job_template" ||
	                                d.unifiedJobTemplate.unified_job_type === "workflow_job") ? null : "none";
                                });
                                
                            thisNode.append("foreignObject")
                                .attr("x", -5)
                                .attr("y", nodeH - 9)
                                .attr("dy", ".35em")
                                .attr("height", "15px")
                                .attr("width", "11px")
	                            .attr("class", "WorkflowChart-pauseIcon")
                                .html(`<span style="color: #ffffff;" class="fa fa-pause"></span>`)
                                .style("display", (d) => {
	                                return d.unifiedJobTemplate &&
	                                (d.unifiedJobTemplate.type === "workflow_approval_template" ||
	                                d.unifiedJobTemplate.unified_job_type === "workflow_approval") ? null : "none";
                                });

                            thisNode.append("rect")
                                .attr("width", nodeW)
                                .attr("height", nodeH)
                                .attr("class", (d) => { return d.isInvalidLinkTarget ? "WorkflowChart-nodeOverlay WorkflowChart-nodeOverlay--disabled" : "WorkflowChart-nodeOverlay WorkflowChart-nodeOverlay--transparent"; })
                                .call(node_click)
                                .on("mouseover", (d) => {
                                    if(d.id !== 1) {
                                        $(`#node-${d.id}`).appendTo(`#aw-workflow-chart-g`);
                                        let resourceName = (d.unifiedJobTemplate && d.unifiedJobTemplate.name) ? d.unifiedJobTemplate.name : "";
                                        if(resourceName && resourceName.length > maxNodeTextLength) {
                                            const sanitizedResourceName = $filter('sanitize')(resourceName);
                                            // When the graph is initially rendered all the links come after the nodes (when you look at the dom).
                                            // SVG components are painted in order of appearance.  There is no concept of z-index, only the order.
                                            // As such, we need to move the nodes after the links so that when the tooltip renders it shows up on top
                                            // of the links and not underneath them.  I tried rendering the links before the nodes but that lead to
                                            // some weird link animation that I didn't care to try to fix.
                                            svgGroup.selectAll("g.WorkflowChart-node").each(() => this.parentNode.appendChild(this));
                                            // After the nodes have been properly placed after the links, we need to make sure that the node that
                                            // the user is hovering over is at the very end of the list.  This way the tooltip will appear on top
                                            // of all other nodes.
                                            svgGroup.selectAll("g.WorkflowChart-node").sort((a) => {
                                                return (a.index !== d.index) ? -1 : 1;
                                            });
                                            // Render the tooltip quickly in the dom and then remove.  This lets us know how big the tooltip is so that we can place
                                            // it properly on the workflow
                                            let tooltipDimensionChecker = $(`<div style='visibility:hidden;font-size:12px;position:absolute;' class='WorkflowChart-tooltipContents'><span>${sanitizedResourceName}</span></div>`);
                                            $('body').append(tooltipDimensionChecker);
                                            let tipWidth = $(tooltipDimensionChecker).outerWidth();
                                            let tipHeight = $(tooltipDimensionChecker).outerHeight();
                                            $(tooltipDimensionChecker).remove();

                                            thisNode.append("foreignObject")
                                                .attr("x", (nodeW / 2) - (tipWidth / 2))
                                                .attr("y", (tipHeight + 15) * -1)
                                                .attr("width", tipWidth)
                                                .attr("height", tipHeight+20)
                                                .attr("class", "WorkflowChart-tooltip")
                                                .html(`<div class='WorkflowChart-tooltipContents'><span>${sanitizedResourceName}</span></div><div class='WorkflowChart-tooltipArrow--down'></div>`);
                                        }

                                        if (scope.graphState.isLinkMode && !d.isInvalidLinkTarget && scope.graphState.addLinkSource !== d.id) {
                                            let sourceNode = d3.select(`#node-${scope.graphState.addLinkSource}`);
                                            const sourceNodeX = d3.transform(sourceNode.attr("transform")).translate[0];
                                            const sourceNodeY = d3.transform(sourceNode.attr("transform")).translate[1];

                                            let targetNode = d3.select(`#node-${d.id}`);
                                            const targetNodeX = d3.transform(targetNode.attr("transform")).translate[0];
                                            const targetNodeY = d3.transform(targetNode.attr("transform")).translate[1];

                                            const startX = sourceNodeX + nodeW/2;
                                            const startY = sourceNodeY + nodeH/2;

                                            const finishX = targetNodeX + nodeW/2;
                                            const finishY = targetNodeY + nodeH/2;

                                            const polylinePoints = {
                                                start: {
                                                    x: startX,
                                                    y: startY
                                                },
                                                third: {
                                                    x: startX + (finishX - startX)/3,
                                                    y: startY + (finishY - startY)/3
                                                },
                                                midpoint: {
                                                    x: startX + (finishX - startX)/2,
                                                    y: startY + (finishY - startY)/2
                                                },
                                                twoThird: {
                                                    x: startX + 2*(finishX - startX)/3,
                                                    y: startY + 2*(finishY - startY)/3
                                                },
                                                finish: {
                                                    x: finishX,
                                                    y: finishY
                                                }
                                            };

                                            $('.WorkflowChart-potentialLink').remove();

                                            svgGroup.insert("polyline", '.WorkflowChart-node')
                                                .attr("class", "WorkflowChart-potentialLink")
                                                .attr("points", `${polylinePoints.start.x},${polylinePoints.start.y} ${polylinePoints.third.x},${polylinePoints.third.y} ${polylinePoints.midpoint.x},${polylinePoints.midpoint.y} ${polylinePoints.twoThird.x},${polylinePoints.twoThird.y} ${polylinePoints.finish.x},${polylinePoints.finish.y}`)
                                                .attr("stroke-dasharray","5,5")
                                                .attr("stroke-width", "2")
                                                .attr("stroke", "#D7D7D7")
                                                .attr('marker-mid', "url(#aw-workflow-chart-arrow)");
                                        }
                                        d3.select(`#node-${d.id}`)
                                            .classed("WorkflowChart-nodeHovering", true);
                                    }
                                })
                                .on("mouseout", (d) => {
                                    $('.WorkflowChart-tooltip').remove();
                                    $('.WorkflowChart-potentialLink').remove();
                                    if(d.id !== 1) {
                                        d3.select(`#node-${d.id}`)
                                            .classed("WorkflowChart-nodeHovering", false);
                                    }
                                });
                            thisNode.append("foreignObject")
                                .attr("x", nodeW - 45)
                                .attr("y", nodeH - 15)
                                .attr("height", "15px")
                                .attr("width", "40px")
                                .attr("dy", ".35em")
                                .attr("class", "WorkflowChart-detailsLink")
                                .style("display", (d) => {
                                    const isApprovalStep = d.unifiedJobTemplate && d.unifiedJobTemplate.unified_job_type === 'workflow_approval';
                                    return d.job &&
                                        !isApprovalStep &&
                                        d.job.status &&
                                        d.job.id ? null : "none";
                                })
                                .on("mousedown", () => d3.event.stopPropagation())
                                .html((d) => {
                                    let href = "";
                                    if (d.job) {
                                        href = `/#/workflow_node_results/${d.job.id}`;
                                    }
                                    return `<a href="${href}">${TemplatesStrings.get('workflow_maker.DETAILS')}</a>`;
                                });
                            thisNode.append("circle")
                                .attr("id", (d) => `node-${d.id}-add`)
                                .attr("cx", nodeW)
                                .attr("r", 10)
                                .attr("class", "WorkflowChart-addCircle WorkflowChart-nodeAddCircle")
                                .style("display", (d) => { return d.id === scope.graphState.nodeBeingAdded || scope.readOnly ? "none" : null; })
                                .call(add_node_without_child)
                                .on("mouseover", (d) => {
                                    d3.select(`#node-${d.id}`)
                                        .classed("WorkflowChart-nodeHovering", true);
                                    d3.select(`#node-${d.id}-add`)
                                        .classed("WorkflowChart-addHovering", true);
                                })
                                .on("mouseout", (d) => {
                                    d3.select(`#node-${d.id}`)
                                        .classed("WorkflowChart-nodeHovering", false);
                                    d3.select(`#node-${d.id}-add`)
                                        .classed("WorkflowChart-addHovering", false);
                                });
                            thisNode.append("path")
                                .attr("class", "WorkflowChart-nodeAddIcon")
                                .style("fill", "white")
                                .attr("transform", `translate(${nodeW}, 0)`)
                                .attr("d", d3.svg.symbol()
                                    .size(60)
                                    .type("cross")
                                )
                                .style("display", (d) => { return d.id === scope.graphState.nodeBeingAdded || scope.readOnly ? "none" : null; })
                                .call(add_node_without_child)
                                .on("mouseover", (d) => {
                                    d3.select(`#node-${d.id}`)
                                        .classed("WorkflowChart-nodeHovering", true);
                                    d3.select(`#node-${d.id}-add`)
                                        .classed("WorkflowChart-addHovering", true);
                                })
                                .on("mouseout", (d) => {
                                    d3.select(`#node-${d.id}`)
                                        .classed("WorkflowChart-nodeHovering", false);
                                    d3.select(`#node-${d.id}-add`)
                                        .classed("WorkflowChart-addHovering", false);
                                });
                            thisNode.append("circle")
                                .attr("id", (d) => `node-${d.id}-link`)
                                .attr("cx", nodeW)
                                .attr("cy", nodeH/2)
                                .attr("r", 10)
                                .attr("class", "WorkflowChart-linkCircle")
                                .style("display", (d) => { return d.id === scope.graphState.nodeBeingAdded || scope.readOnly ? "none" : null; })
                                .call(add_link)
                                .on("mouseover", (d) => {
                                    d3.select(`#node-${d.id}`)
                                        .classed("WorkflowChart-nodeHovering", true);
                                    d3.select(`#node-${d.id}-link`)
                                        .classed("WorkflowChart-linkButtonHovering", true);
                                })
                                .on("mouseout", (d) => {
                                    d3.select(`#node-${d.id}`)
                                        .classed("WorkflowChart-nodeHovering", false);
                                    d3.select(`#node-${d.id}-link`)
                                        .classed("WorkflowChart-linkButtonHovering", false);
                                });
                          thisNode.append("foreignObject")
                               .attr("x", nodeW - 6)
                               .attr("y", nodeH/2 - 9)
                               .attr("height", "17px")
                               .attr("width", "13px")
                               .style("font-size","14px")
                               .html(`<span class="fa fa-link"></span>`)
                               .attr("class", "WorkflowChart-nodeLinkIcon")
                               .style("display", (d) => { return d.id === scope.graphState.nodeBeingAdded || scope.readOnly ? "none" : null; })
                               .call(add_link)
                               .on("mouseover", (d) => {
                                   d3.select(`#node-${d.id}`)
                                       .classed("WorkflowChart-nodeHovering", true);
                                   d3.select(`#node-${d.id}-link`)
                                       .classed("WorkflowChart-linkButtonHovering", true);
                               })
                               .on("mouseout", (d) => {
                                   d3.select(`#node-${d.id}`)
                                       .classed("WorkflowChart-nodeHovering", false);
                                   d3.select(`#node-${d.id}-link`)
                                       .classed("WorkflowChart-linkButtonHovering", false);
                               });
                            thisNode.append("circle")
                                .attr("id", (d) => `node-${d.id}-remove`)
                                .attr("cx", nodeW)
                                .attr("cy", nodeH)
                                .attr("r", 10)
                                .attr("class", "WorkflowChart-nodeRemoveCircle")
                                .style("display", (d) => { return (d.id === 1 || d.id === scope.graphState.nodeBeingAdded || scope.readOnly) ? "none" : null; })
                                .call(remove_node)
                                .on("mouseover", (d) => {
                                    d3.select(`#node-${d.id}`)
                                        .classed("WorkflowChart-nodeHovering", true);
                                    d3.select(`#node-${d.id}-remove`)
                                        .classed("removeHovering", true);
                                })
                                .on("mouseout", (d) => {
                                    d3.select(`#node-${d.id}`)
                                        .classed("WorkflowChart-nodeHovering", false);
                                    d3.select(`#node-${d.id}-remove`)
                                        .classed("removeHovering", false);
                                });
                            thisNode.append("path")
                                .attr("class", "WorkflowChart-nodeRemoveIcon")
                                .style("fill", "white")
                                .attr("transform", `translate(${nodeW}, ${nodeH}) rotate(-45)`)
                                .attr("d", d3.svg.symbol()
                                    .size(60)
                                    .type("cross")
                                )
                                .style("display", (d) => { return (d.id === 1 || d.id === scope.graphState.nodeBeingAdded || scope.readOnly) ? "none" : null; })
                                .call(remove_node)
                                .on("mouseover", (d) => {
                                    d3.select(`#node-${d.id}`)
                                        .classed("WorkflowChart-nodeHovering", true);
                                    d3.select(`#node-${d.id}-remove`)
                                        .classed("removeHovering", true);
                                })
                                .on("mouseout", (d) => {
                                    d3.select(`#node-${d.id}`)
                                        .classed("WorkflowChart-nodeHovering", false);
                                    d3.select(`#node-${d.id}-remove`)
                                        .classed("removeHovering", false);
                                });

                            thisNode.append("circle")
                                .attr("class", (d) => {
                                    let statusClasses = ["WorkflowChart-nodeStatus"];
        
                                    if(d.job){
                                        switch(d.job.status) {
                                            case "pending":
                                            case "waiting":
                                            case "running":
                                                statusClasses.push("WorkflowChart-nodeStatus--running");
                                                break;
                                            case "successful":
                                                statusClasses.push("WorkflowChart-nodeStatus--success");
                                                break;
                                            case "failed":
                                            case "error":
                                                statusClasses.push("WorkflowChart-nodeStatus--failed");
                                                break;
                                            case "canceled":
                                                statusClasses.push("WorkflowChart-nodeStatus--canceled");
                                                break;
                                        }
                                    }
        
                                    return statusClasses.join(' ');
                                })
                                .style("display", (d) => { return d.job && d.job.status ? null : "none"; })
                                .attr("cy", 10)
                                .attr("cx", 10)
                                .attr("r", 6)
                                .each(function(d) {
                                    if(d.job && d.job.status && (d.job.status === "pending" || d.job.status === "waiting" || d.job.status === "running")) {
                                        // Pulse the circle
                                        let circle = d3.select(this);
                                        (function repeat() {
                                            circle = circle.transition()
                                                .duration(2000)
                                                .attr("r", 6)
                                                .transition()
                                                .duration(2000)
                                                .attr("r", 0)
                                                .ease('sine')
                                                .each("end", repeat);
                                        })();
                                    }
                                });

                            thisNode.append("foreignObject")
                                 .attr("x", 5)
                                 .attr("y", 43)
                                 .style("font-size","0.7em")
                                 .attr("class", "WorkflowChart-elapsed")
                                 .html((d) => {
                                     if(d.job && d.job.elapsed) {
                                         let elapsedMs = d.job.elapsed * 1000;
                                         let elapsedMoment = moment.duration(elapsedMs);
                                         let paddedElapsedMoment = Math.floor(elapsedMoment.asHours()) < 10 ? "0" + Math.floor(elapsedMoment.asHours()) : Math.floor(elapsedMoment.asHours());
                                         let elapsedString = paddedElapsedMoment + moment.utc(elapsedMs).format(":mm:ss");
                                         return `<div class=\"WorkflowChart-elapsedHolder\"><span>${elapsedString}</span></div>`;
                                     }
                                     else {
                                         return "";
                                     }
                                 })
                                 .style("display", (d) => { return (d.job && d.job.elapsed) ? null : "none"; });
                        }
                    });

                    if(scope.graphState.arrayOfNodesForChart && scope.graphState.arrayOfNodesForChart.length > 1 && !graphLoaded) {
                        zoomToFitChart();
                    }

                    graphLoaded = true;

                    // This will make sure that all the link elements appear before the nodes in the dom
                    svgGroup.selectAll(".WorkflowChart-node").order();
                }
                else if(!scope.watchDimensionsSet){
                    scope.watchDimensionsSet = scope.$watch('dimensionsSet', () => {
                        if(scope.dimensionsSet) {
                            scope.watchDimensionsSet();
                            scope.watchDimensionsSet = null;
                            updateGraph();
                        }
                    });
                }
            };

            function add_node_without_child() {
                this.on("click", (d) => {
                    if(!scope.readOnly && !scope.graphState.isLinkMode) {
                        scope.addNodeWithoutChild({
                            parent: d
                        });
                    }
                });
            }

            function add_node_with_child() {
                this.on("click", (d) => {
                    if(!scope.readOnly && !scope.graphState.isLinkMode && d.edgeType !== 'placeholder') {
                        scope.addNodeWithChild({
                            link: d
                        });
                    }
                });
            }

            function remove_node() {
                this.on("click", (d) => {
                    if(d.id !== 1 && !scope.readOnly && !scope.graphState.isLinkMode) {
                        scope.deleteNode({
                            nodeToDelete: d
                        });
                    }
                });
            }

            function node_click() {
                this.on("click", (d) => {
                    if(d.id !== scope.graphState.nodeBeingAdded){
                        if(scope.graphState.isLinkMode && !d.isInvalidLinkTarget && scope.graphState.addLinkSource !== d.id) {
                            $('.WorkflowChart-potentialLink').remove();
                            scope.selectNodeForLinking({
                                nodeToStartLink: d
                            });
                        } else if(!scope.graphState.isLinkMode) {
                            scope.editNode({
                                nodeToEdit: d
                            });
                        }

                    }
                });
            }

            function edit_link() {
                this.on("click", (d) => {
                    if(!scope.graphState.isLinkMode && d.source.id !== 1 && d.source.id !== scope.graphState.nodeBeingAdded && d.target.id !== scope.graphState.nodeBeingAdded && scope.mode !== 'details'){
                        scope.editLink({
                            linkToEdit: d
                        });
                    }
                });
            }

            function add_link() {
                this.on("click", (d) => {
                    if (!scope.readOnly && !scope.graphState.isLinkMode) {
                        scope.selectNodeForLinking({
                            nodeToStartLink: d
                        });
                    }
                });
            }

            scope.$on('refreshWorkflowChart', () => {
                if(scope.graphState) {
                    updateGraph();
                }
            });

            scope.$on('panWorkflowChart', (evt, params) => {
                manualPan(params.direction);
            });

            scope.$on('resetWorkflowChart', () => {
                resetZoomAndPan();
            });

            scope.$on('zoomWorkflowChart', (evt, params) => {
                manualZoom(params.zoom);
            });

            scope.$on('zoomToFitChart', () => {
                zoomToFitChart();
            });

            let clearWatchGraphState = scope.$watch('graphState.arrayOfNodesForChart', (newVal) => {
                if(newVal) {
                    updateGraph();
                    clearWatchGraphState();
                }
            });

            function onResize(){
                let dimensions = calcAvailableScreenSpace();

                $('.WorkflowMaker-chart').css("width", dimensions.width);
                $('.WorkflowMaker-chart').css("height", dimensions.height);
            }

            function cleanUpResize() {
                angular.element($window).off('resize', onResize);
            }

            $timeout(() => {
                let dimensions = calcAvailableScreenSpace();

                windowHeight = dimensions.height;
                windowWidth = dimensions.width;

                $('.WorkflowMaker-chart').css("height", windowHeight);

                scope.dimensionsSet = true;

                line = d3.svg.line()
                    .x((d) => {
                        return d.x;
                    })
                    .y((d) => {
                        return d.y;
                    });

                zoomObj = d3.behavior.zoom().scaleExtent([0.1, 2]);

                baseSvg = d3.select(element[0]).append("svg")
                    .attr("class", "WorkflowChart-svg")
                    .call(zoomObj
                        .on("zoom", naturalZoom)
                    );

                svgGroup = baseSvg.append("g")
                    .attr("id", "aw-workflow-chart-g")
                    .attr("transform", `translate(0, ${(windowHeight/2 - rootH/2 - startNodeOffsetY)})`);

                const defs = baseSvg.append("defs");

                  defs.append("marker")
                    .attr("id", "aw-workflow-chart-arrow")
                    .attr("viewBox", "0 -5 10 10")
                    .attr("refX", 5)
                    .attr("markerWidth", 6)
                    .attr("markerHeight", 6)
                    .attr("orient", "auto")
                  .append("path")
                    .attr("d", "M0,-5L10,0L0,5")
                    .attr('fill', "#D7D7D7");
                        });

            if(scope.mode === 'details') {
                angular.element($window).on('resize', onResize);
                scope.$on('$destroy', cleanUpResize);

                scope.$on('workflowDetailsResized', () => {
                    $('.WorkflowMaker-chart').hide();
                    $timeout(() => {
                        onResize();
                        $('.WorkflowMaker-chart').show();
                    });
                });
            }
            else {
                scope.$on('workflowMakerModalResized', () => {
                    let dimensions = calcAvailableScreenSpace();

                    $('.WorkflowMaker-chart').css("width", dimensions.width);
                    $('.WorkflowMaker-chart').css("height", dimensions.height);
                });
            }
        }
    };
}];
