"use strict";

// -------------------------------------------------------------------------
  // OPTIONS:

  // http://visjs.org/docs/network/#modules
  // http://visjs.org/docs/network/edges.html#
  // http://visjs.org/docs/network/physics.html#

var visjs_options = {
  nodes: {shape: 'box'},
  edges: {
    arrows: {
      to: {enabled: true, scaleFactor:0.75, type:'arrow'},
      // to: {enabled: false, scaleFactor:0.5, type:'bar'},
      middle: {enabled: false, scaleFactor:1, type:'arrow'},
      from: {enabled: false, scaleFactor:0.3, type:'arrow'}
      // from: {enabled: false, scaleFactor:0.5, type:'arrow'}
    },
    arrowStrikethrough: true,
    chosen: true,
    color: {
      color:'red',
      highlight:'#848484',
      hover: '#848484',
      inherit: 'from',
      opacity:1.0
    },
    dashes: false,
    font: {
      color: '#343434',
      size: 14, // px
      face: 'arial',
      background: 'none',
      strokeWidth: 2, // px
      strokeColor: '#ffffff',
      align: 'horizontal',
      multi: false,
      vadjust: 0,
      bold: {
        color: '#343434',
        size: 14, // px
        face: 'arial',
        vadjust: 0,
        mod: 'bold'
      },
      ital: {
        color: '#343434',
        size: 14, // px
        face: 'arial',
        vadjust: 0,
        mod: 'italic'
      },
      boldital: {
        color: '#343434',
        size: 14, // px
        face: 'arial',
        vadjust: 0,
        mod: 'bold italic'
      },
      mono: {
        color: '#343434',
        size: 15, // px
        face: 'courier new',
        vadjust: 2,
        mod: ''
      }
    }
  },
  // http://visjs.org/docs/network/physics.html#
  physics: {
    enabled: true,
    barnesHut: {
      gravitationalConstant: -2000,
      centralGravity: 0.3,
      // springLength: 95,
      springLength: 95,
      springConstant: 0.04,
      damping: 0.09,
      avoidOverlap: 0
    },
    forceAtlas2Based: {
      gravitationalConstant: -50,
      centralGravity: 0.005,
      springConstant: 0.08,
      springLength: 100,
      damping: 0.4,
      avoidOverlap: 0
    },
    repulsion: {
      centralGravity: 0.2,
      springLength: 200,
      springConstant: 0.05,
      nodeDistance: 100,
      damping: 0.09
    },
    hierarchicalRepulsion: {
      centralGravity: 0.0,
      springLength: 100,
      springConstant: 0.01,
      nodeDistance: 120,
      damping: 0.09
    },
    maxVelocity: 50,
    minVelocity: 0.1,
    solver: 'barnesHut',
    stabilization: {
      enabled: true,
      iterations: 500,
      updateInterval: 100,
      onlyDynamicEdges: false,
      fit: true
    },
    timestep: 0.5,
    adaptiveTimestep: true
  },
  groups: {
    post: {
      shape: 'circle',
      size: 3,
      color: {
        border: 'black',
        background: 'blue',
        highlight: {border: 'grey', background: 'lightblue'}
      }
    }
  },
  interaction: { navigationButtons: false },
  // configure: { enabled: false },
  layout: { 
    // randomSeed:42,
    improvedLayout: false
  }
};


window.addEventListener('load', function () {

  var container = document.getElementById('mynetwork');
  var data = {
    nodes: graph_json.nodes,
    edges: graph_json.edges
  };
  console.log("Graph num nodes:", data.nodes.length, ' Graph num edges:', data.edges.length)
  var network = new vis.Network(container, data, visjs_options);

  network.on("stabilizationProgress", function (params) {
    const progress = document.getElementById('netprogress');
    const value = parseInt(params.iterations / params.total * 100)
    progress.style.setProperty("--progressbar", `${value}%`);
  });

  network.once("stabilizationIterationsDone", function () {
    const progress = document.getElementById('netprogress');
    progress.style.setProperty("--progressbar", `100%`);
    progress.style.opacity = 0;
    setTimeout(function (progress) {
      progress.style.display = "none";
    }.bind(null,progress), 500);
  });

  // network.on("select", function (params) {
  //   params.event = "[original event]";
  //   // document.getElementById("eventSpanHeading").innerText = "Click event:";
  //   // document.getElementById("eventSpanContent").innerText = JSON.stringify(
  //   //   params,
  //   //   null,
  //   //   4
  //   // );
  //   console.log("select event, getNodeAt returns: " +
  //       this.getNodeAt(params.pointer.DOM));
  //   console.log( network.getSelection())
  // });

});