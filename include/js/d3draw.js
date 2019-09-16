drawgraph = (container, graph, width=300, height=300) => {

  /* This isn't used to zawinskify the look. Colors come from css instead. Less portable. */
  var nodeColor = d3.scaleOrdinal(d3.schemeDark2);

  var prNorm = d3.scaleLinear()
    .domain(d3.extent(graph.nodes.map(d => d.pagerank)))

  var eicNorm = d3.scaleLinear()
    .domain(d3.extent(graph.nodes.map(d => d.eic)))

  // Change this to favor PageRank or EIC
  var nodeRadius = d3.scaleLinear()
    .domain([0, 2]) /* Not necessarily true */
    .range([10, 30]);  /* min/max size of nodes in px */

  var linkWidth = d3.scalePow()
    .domain(d3.extent(graph.links.map(d => d.betweenness)))
    .exponent(2)
    .range([1, 3]);  /* min/max size of links in px */

  var linkAlpha = d3.scaleLinear()
    .domain(d3.extent(graph.links.map(d => d.betweenness)))
    .range([0.25, 0.9]);

  dragstarted = (d) => {
    if (!d3.event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  dragged = (d) => {
    d.fx = d3.event.x;
    d.fy = d3.event.y;
  }

  dragended = (d) => {
    if (!d3.event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  ticked = (d) => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);
    node
      .attr('transform', d => {
        return 'translate(' + d.x + ',' + d.y + ')';
      })
  }

  var nclut = {}; // node-community lookup table
  graph.nodes.forEach(d => {
    d.radius = nodeRadius(prNorm(d.pagerank) + eicNorm(d.eic));
    nclut[d.id] = d.community;
  })

  var div = d3.select("body").append("div")	
    .attr("class", "tooltip")				
    .style("opacity", 0);

  var svg = d3.select(container).select('svg');
  if (svg.empty()) {
      svg = d3.select(container).append('svg')
        .attr('width', width)
        .attr('height', height);
  }

  // https://github.com/gopeter/semantic-diagrams/blob/ad630ba1566bbaba622e317732d9d90a2f281fab/static/js/app.js#L132
  // https://www.w3.org/TR/SVG2/linking.html#URLandURI
  $('svg').attr('xmlns', 'http://www.w3.org/2000/svg');

  var simulation = d3.forceSimulation()
      .force('center',  d3.forceCenter(width/2, height/2))
      .force('collide', d3.forceCollide()
            .radius(d => d.radius+2)
      )
      .force('link',    d3.forceLink()
            .id(d => d.id)
            .distance(d => {
                var dist = 30
                if(d.source.radius + d.target.radius > 0) {
                    // guarding against something that happened once. fishy.
                    dist = 2.5*(d.source.radius+d.target.radius)
                }
                if(d.source.community != d.target.community) {
                    dist *= 3
                }
                if(isNaN(dist)) {
                    return 30
                } // more fish
                return dist;
            })
      )
      .force('charge',  d3.forceManyBody()
            .strength(-120)
      );

  var link = svg.append('g')
    .attr('class', 'links')
    .selectAll('line')
    .data(graph.links)
    .enter().append('line')
      // Either method, the link color is the same as the 'source'
      /* zawinskification
      .attr('stroke', d => nodeColor(nclut[d.source]))  */
      .attr('class', d => 'comm_' + nclut[d.source])
      .style('stroke-width', d => linkWidth(d.betweenness))
      .style('stroke-opacity', d => linkAlpha(d.betweenness));

  var node = svg.append('g')
    .attr('class', 'nodes')
    .selectAll('g')
    .data(graph.nodes)
    .enter().append('a')
      .attr("xlink:href", d => 'https://www.jwz.org/blog/tag/' + d.id + '/')

    node.append('g')

  var circles = node.append('circle')
    .attr('class', d => 'comm_' + d.community)
    .attr('r', d => nodeRadius(prNorm(d.pagerank) + eicNorm(d.eic)))
    /* zawinskification
    .attr('fill', d => nodeColor(d.community))
    .attr('stroke', d => d3.rgb(nodeColor(d.community)).darker()) */
    .on("mouseover", d => {
        div.transition()		
          .duration(200)		
          .style("opacity", .9);		
        div.html(() =>
            '<strong>id: ' + d.id + '</strong>' +
            '<br>pagerank: ' + d.pagerank +
            '<br>eic: ' + d.eic +
            '<br>community: ' + d.community
          )
          .style("left", (d3.event.pageX + 18) + "px")		
          .style("top", (d3.event.pageY - 28) + "px");	
    })					
    .on("mouseout", function(d) {		
        div.transition()		
          .duration(500)		
          .style("opacity", 0);	
    })
    .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));


  simulation
    .nodes(graph.nodes)
    .on('tick', ticked);

  simulation.force('link')
    .links(graph.links);

};
