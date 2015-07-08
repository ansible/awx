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
                    createGraph(data);
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

            function createGraph(data) {
                if(data.hosts.total+data.hosts.failed>0){
                    data = [
                        {   "label": "Successful",
                            "color": "#60D66F",
                            "value" : data.hosts.total - data.hosts.failed
                        } ,
                        {   "label": "Failed",
                            "color" : "#ff5850",
                            "value" : data.hosts.failed
                        }
                    ];

                    host_pie_chart = nv.models.pieChart()
                        .margin({bottom: 15})
                        .x(function(d) { return d.label; })
                        .y(function(d) { return d.value; })
                        .showLabels(true)
                        .growOnHover(false)
                        .labelThreshold(0.01)
                        .tooltipContent(function(x, y) {
                            return '<b>'+x+'</b>'+ '<p>' +  Math.floor(y.replace(',','')) + ' Hosts ' +  '</p>';
                        })
                        .labelType("percent")
                        .color(['#60D66F', '#ff5850']);

                    d3.select(element.find('svg')[0])
                        .datum(data)
                        .transition().duration(350)
                        .call(host_pie_chart)
                        .style({
                            "font-family": 'Open Sans',
                            "font-style": "normal",
                            "font-weight":400,
                            "src": "url(/static/fonts/OpenSans-Regular.ttf)"
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
