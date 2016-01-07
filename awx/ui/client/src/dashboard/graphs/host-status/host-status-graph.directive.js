/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    [   '$compile',
        '$window',
        'adjustGraphSize',
        'templateUrl',
        HostStatusGraph,
    ];

function HostStatusGraph($compile, $window, adjustGraphSize, templateUrl) {
        return {
            restrict: 'E',
            link: link,
            templateUrl: templateUrl('dashboard/graphs/host-status/host_status_graph')
        };

        function link(scope, element, attr) {
            var host_pie_chart;

            scope.$watch(attr.data, function(data) {
                if (data && data.hosts) {
                    scope.data = data;
                    createGraph();
                }
            });

            function adjustHostGraphSize() {
                if (angular.isUndefined(host_pie_chart)) {
                    return;
                }
                var parentHeight = element.parent().parent().height();
                var toolbarHeight = element.find('.toolbar').height();
                var container = element.find('svg').parent();
                var margins = host_pie_chart.margin();

                var newHeight = parentHeight - toolbarHeight - margins.bottom;

                $(container).height(newHeight);

                host_pie_chart.update();
            }

            angular.element($window).on('resize', adjustHostGraphSize);
            $(".DashboardGraphs-graph--hostStatusGraph").resize(adjustHostGraphSize);

            element.on('$destroy', function() {
                angular.element($window).off('resize', adjustHostGraphSize);
                $(".DashboardGraphs-graph--hostStatusGraph").removeResize(adjustHostGraphSize);
            });

            function createGraph() {
                var data, colors, color;
                if(scope.data.hosts.total+scope.data.hosts.failed>0){
                    if(scope.status === "successful"){
                        data = [
                        {   "label": "SUCCESSFUL",
                            "color": "#3CB878",
                            "value" : scope.data.hosts.total - scope.data.hosts.failed
                        }];
                        colors = ['#3cb878'];
                    }
                    else if (scope.status === "failed"){
                        data = [{   "label": "FAILED",
                            "color" : "#ff5850",
                            "value" : scope.data.hosts.failed
                        }];
                        colors = ['#ff5850'];
                    }
                    else {
                        data = [
                            {   "label": "SUCCESSFUL",
                                "color": "#3CB878",
                                "value" : scope.data.hosts.total - scope.data.hosts.failed
                            } ,
                            {   "label": "FAILED",
                                "color" : "#ff5850",
                                "value" : scope.data.hosts.failed
                            }
                        ];
                        colors = ['#3cb878', '#ff5850'];
                    }

                    host_pie_chart = nv.models.pieChart()
                        .margin({bottom: 15})
                        .x(function(d) {
                            return d.label +': '+ Math.round((d.value/scope.data.hosts.total)*100) + "%";
                        })
                        .y(function(d) { return d.value; })
                        .showLabels(true)
                        .showLegend(false)
                        .growOnHover(false)
                        .labelThreshold(0.01)
                        .tooltipContent(function(x, y) {
                            return '<p>'+x+'</p>'+ '<p>' +  Math.floor(y.replace(',','')) + ' HOSTS ' +  '</p>';
                        })
                        .color(colors);

                    d3.select(element.find('svg')[0])
                        .datum(data)
                        .transition().duration(350)
                        .call(host_pie_chart)
                        .style({
                            "font-family": 'Open Sans',
                            "font-style": "normal",
                            "font-weight":400,
                            "src": "url(/static/assets/OpenSans-Regular.ttf)"
                        });
                    if(scope.status === "failed"){
                        color = "#ff5850";
                    }
                    else{
                        color = "#3CB878";
                    }

                    d3.select(element.find(".nv-label text")[0])
                        .attr("class", "DashboardGraphs-hostStatusLabel--successful")
                        .style({
                            "font-family": 'Open Sans',
                            "text-anchor": "start",
                            "font-size": "16px",
                            "text-transform" : "uppercase",
                            "fill" : color,
                            "src": "url(/static/assets/OpenSans-Regular.ttf)"
                        });
                    d3.select(element.find(".nv-label text")[1])
                        .attr("class", "DashboardGraphs-hostStatusLabel--failed")
                        .style({
                            "font-family": 'Open Sans',
                            "text-anchor" : "end !imporant",
                            "font-size": "16px",
                            "text-transform" : "uppercase",
                            "fill" : "#ff5850",
                            "src": "url(/static/assets/OpenSans-Regular.ttf)"
                        });

                    adjustGraphSize();
                    return host_pie_chart;
                }
                else{
                    // This should go in a template or something
                    // but I'm at the end of a card and need to get this done.
                    // We definitely need to refactor this, I'm letting
                    // good enough be good enough for right now.
                    var notFoundContainer = $('<div></div>');
                    notFoundContainer.css({
                        'text-align': 'center',
                        'width': '100%',
                        'padding-top': '2em'
                    });

                    notFoundContainer.text('No host data');

                    element.find('svg').replaceWith(notFoundContainer);
                }


            }
        }
    }
