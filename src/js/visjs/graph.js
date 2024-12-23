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
      springLength: 95,
      springConstant: 0.07,
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
    solver: 'repulsion',
    stabilization: {
      enabled: true,
      iterations: 500,
      updateInterval: 10,
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
        border: '#0c0ca5',
        background: 'blue',
        highlight: {border: 'grey', background: 'lightblue'}
      }
    }
  },
  interaction: { navigationButtons: false },
  // configure: { enabled: false },
  layout: { 
    randomSeed:0.6154292573936662,
    improvedLayout: false
  }
};


var network = null;

function moveViewToNode(nodeID, markSelected = false) {
  var pos;
  try {
    pos = network.getPosition(nodeID);
  } catch (err) {
    return false;
  }
  if (markSelected)
    network.selectNodes( [nodeID]);
  network.moveTo({position: pos, animation:true, scale: network.getScale() < 0.3 ? 0.8 : undefined});
  return true;
}

window.addEventListener('load', function () {

  const nodes = new vis.DataSet(graph_json.nodes);
  const edges = new vis.DataSet(graph_json.edges);
  var authorSrchValue = "";
  const nodesFilter = (node) => {
    if (authorSrchValue === "") {
      return true;
    }
    switch (node.group) {
      case "author":
        // return node.title === authorSrchValue;
        return node.label.startsWith(authorSrchValue);
      default:
        return false;
    }
  };
  const nodesView = new vis.DataView(nodes, { filter: nodesFilter });
  const edgesView = new vis.DataView(edges, { });
  const author_srchbox = document.getElementById("srch-author");
  const infodiv = document.getElementById('selnodeinfo');
  const authorSrchResults = document.getElementById('author-srch-res');

  console.log("Graph num nodes:", nodes.length, ' Graph num edges:', edges.length)
  const container = document.getElementById('mynetwork');
  network = new vis.Network(container, { nodes: nodesView, edges: edgesView }, visjs_options);


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
    //in case we opened with browser "back button" which stores history of input values
    author_srchbox.dispatchEvent(new Event("input"));

    //graph settings pane
    const net_cnt = document.getElementById('graph-stngs');
    let settings_pane = document.createElement('div');
    settings_pane.className = 'graph-settings';
    settings_pane.innerHTML = '<div class="checkbox-cnt"><input type="checkbox" id="phys-toggle">Симуляция физики</div>';
    net_cnt.prepend(settings_pane);
    const phys_toggle = document.getElementById('phys-toggle');
    phys_toggle.checked = visjs_options.physics.enabled;
    phys_toggle.addEventListener("input", (e) => {
      network.setOptions( { physics: e.target.checked } );
    });
  });


  network.on("configChange", function() {
    const phys_toggle = document.getElementById('phys-toggle');
    if (!phys_toggle)
      return;
    phys_toggle.checked = network.options.physics;
  });

  network.on("select", function (params) {
    if (!network.getSelectedNodes().length) return;
    const selnode = nodes.get( network.getSelectedNodes()[0] )
    params.event = "[original event]";
    if (selnode.group && selnode.group == 'post') {
      let txt = '<dl><dt>Статья</dt><dd class="dd-title">'
      txt += selnode.localName ? ('<a href="../' + selnode.localName + '">' + selnode.title + '</a>') : selnode.title;
      txt += `&nbsp;${selnode.bookmarked_count ? ('<span title="Добавили в закладки"><span class="bookmarked">'+selnode.bookmarked_count+'</span></span>') : ''}</dd>`;
      console.log( selnode.pubdate, selnode.pubdate && selnode.pubdate.length>2 )
      if (selnode.pubdate && selnode.pubdate.length > 2)
        txt += `<dt>Дата публикации</dt><dd class="dd-pubdate">${selnode.pubdate}</dd>`;
      txt += `<dt>Оригинальная статья</dt><dd><a href="${selnode.url}">Источник</a></dd>`;
      txt += `<dt>Автор</dt><dd class="author" onclick="moveViewToNode('${selnode.author}')">${selnode.author}</dd></dl>\n`;
      infodiv.innerHTML = txt ;
    }
    else {infodiv.innerHTML =''}

  });

  author_srchbox.addEventListener("input", (e) => {
    e.stopPropagation();
    e.preventDefault();
    authorSrchValue = e.target.value.trim().toLowerCase();
    if (!authorSrchValue.length) {
      authorSrchResults.innerHTML = '';
      return;
    }
    // nodesView.refresh();
    var found = nodes.get({filter: function (item) {
      if (item.label && item.group && item.group == 'author')
        return (item.label.toLowerCase().startsWith(authorSrchValue));
      else
        return false;
    }});
    var newres = '';
    found.forEach( (item) => {newres += `<pre class="author">${item.label}</pre>`})
    authorSrchResults.innerHTML = newres;
  });
  
  authorSrchResults.addEventListener("click", (e) => {
    if (e.target['tagName'] !== "PRE")
      return;
    const el_id = e.target.innerText;
    e.stopPropagation();
    e.preventDefault();
    moveViewToNode(el_id, true);
  });

});