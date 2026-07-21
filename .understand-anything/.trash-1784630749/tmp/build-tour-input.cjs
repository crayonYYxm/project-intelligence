// Build tour input JSON from arch-input.json + layers.json
// Produces ua-tour-input.json with {nodes, edges, layers} where nodes are file-level only.
const fs = require('fs');
const path = require('path');

const UA_DIR = '/Users/xumeng/Desktop/code/project-intelligence/.ua';
const archInput = JSON.parse(fs.readFileSync(path.join(UA_DIR, 'tmp/arch-input.json'), 'utf8'));
const layersRaw = JSON.parse(fs.readFileSync(path.join(UA_DIR, 'intermediate/layers.json'), 'utf8'));

const nodes = (archInput.fileNodes || []).map(n => ({
  id: n.id,
  type: n.type,
  name: n.name,
  filePath: n.filePath,
  summary: n.summary || ''
}));

const nodeIds = new Set(nodes.map(n => n.id));

// Filter edges: only keep edges where BOTH source and target are file-level nodes.
// (arch-input.json contains function/class-level edges too, which reference IDs not in fileNodes.)
const allEdges = (archInput.allEdges || []).filter(e =>
  nodeIds.has(e.source) && nodeIds.has(e.target)
).map(e => ({
  source: e.source,
  target: e.target,
  type: e.type
}));

// Layers: strip nodeIds per dispatch instructions
const layers = (layersRaw || []).map(l => ({
  id: l.id,
  name: l.name,
  description: l.description
}));

const out = { nodes, edges: allEdges, layers };
fs.writeFileSync(path.join(UA_DIR, 'tmp/ua-tour-input.json'), JSON.stringify(out, null, 2));
console.log('nodes:', nodes.length, 'edges (file-level only):', allEdges.length, 'layers:', layers.length);
