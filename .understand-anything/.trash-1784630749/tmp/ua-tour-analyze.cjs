#!/usr/bin/env node
'use strict';
// Tour topology analysis script.
// Usage: node ua-tour-analyze.js <input.json> <output.json>

const fs = require('fs');

function main() {
  const [,, inPath, outPath] = process.argv;
  if (!inPath || !outPath) {
    console.error('Usage: node ua-tour-analyze.js <input.json> <output.json>');
    process.exit(1);
  }

  const raw = fs.readFileSync(inPath, 'utf8');
  const data = JSON.parse(raw);
  const nodes = Array.isArray(data.nodes) ? data.nodes : [];
  const edges = Array.isArray(data.edges) ? data.edges : [];
  const layers = Array.isArray(data.layers) ? data.layers : [];

  const nodeById = new Map();
  for (const n of nodes) nodeById.set(n.id, n);

  // --- A. Fan-in ranking (edges pointing TO a node) ---
  const fanIn = new Map();
  for (const n of nodes) fanIn.set(n.id, 0);
  for (const e of edges) {
    if (fanIn.has(e.target)) fanIn.set(e.target, fanIn.get(e.target) + 1);
  }
  const fanInRanking = nodes
    .map(n => ({ id: n.id, fanIn: fanIn.get(n.id), name: n.name, summary: n.summary }))
    .sort((a, b) => b.fanIn - a.fanIn)
    .slice(0, 20);

  // --- B. Fan-out ranking (edges pointing FROM a node) ---
  const fanOut = new Map();
  for (const n of nodes) fanOut.set(n.id, 0);
  for (const e of edges) {
    if (fanOut.has(e.source)) fanOut.set(e.source, fanOut.get(e.source) + 1);
  }
  const fanOutRanking = nodes
    .map(n => ({ id: n.id, fanOut: fanOut.get(n.id), name: n.name }))
    .sort((a, b) => b.fanOut - a.fanOut)
    .slice(0, 20);

  // --- C. Entry point candidates ---
  const codeEntryNames = new Set([
    'index.ts','index.js','main.ts','main.js','app.ts','app.js','server.ts','server.js',
    'mod.rs','main.go','main.py','main.rs','manage.py','app.py','wsgi.py','asgi.py',
    'run.py','__main__.py','Application.java','Main.java','Program.cs','config.ru',
    'index.php','App.swift','Application.kt','main.cpp','main.c'
  ]);

  const fanOutVals = nodes.map(n => fanOut.get(n.id)).filter(v => true).sort((a, b) => a - b);
  const fanInVals = nodes.map(n => fanIn.get(n.id)).sort((a, b) => a - b);
  // top 10% fan-out threshold
  const top10pctIdx = Math.floor(fanOutVals.length * 0.9);
  const fanOutTop10Threshold = fanOutVals[top10pctIdx] || 0;
  // bottom 25% fan-in threshold
  const bot25pctIdx = Math.floor(fanInVals.length * 0.25);
  const fanInBot25Threshold = fanInVals[bot25pctIdx] || 0;

  const entryScores = [];
  for (const n of nodes) {
    let score = 0;
    if (n.type === 'document') {
      if (n.filePath === 'README.md') score += 5;
      else if (n.filePath && n.filePath.split('/').length === 1 && n.name && n.name.endsWith('.md')) score += 2;
    } else {
      // code files (file / service / etc.)
      if (codeEntryNames.has(n.name)) score += 3;
      const depth = n.filePath ? n.filePath.split('/').length - 1 : 99;
      if (depth <= 1) score += 1;
      if (fanOut.get(n.id) >= fanOutTop10Threshold && fanOutTop10Threshold > 0) score += 1;
      if (fanIn.get(n.id) <= fanInBot25Threshold) score += 1;
    }
    if (score > 0) entryScores.push({ id: n.id, score, name: n.name, summary: n.summary, type: n.type });
  }
  entryScores.sort((a, b) => b.score - a.score);
  const entryPointCandidates = entryScores.slice(0, 5);

  // --- D. BFS from top CODE entry point ---
  const codeCandidate = entryScores.find(c => c.type !== 'document');
  const startNode = codeCandidate ? codeCandidate.id : (nodes[0] && nodes[0].id);

  // adjacency: forward direction, only imports + calls
  const adj = new Map();
  for (const n of nodes) adj.set(n.id, []);
  for (const e of edges) {
    if (e.type === 'imports' || e.type === 'calls') {
      if (adj.has(e.source) && nodeById.has(e.target)) adj.get(e.source).push(e.target);
    }
  }

  const bfsTraversal = { startNode, order: [], depthMap: {}, byDepth: {} };
  if (startNode) {
    const visited = new Set([startNode]);
    const queue = [{ id: startNode, depth: 0 }];
    bfsTraversal.depthMap[startNode] = 0;
    while (queue.length) {
      const { id, depth } = queue.shift();
      bfsTraversal.order.push(id);
      if (!bfsTraversal.byDepth[depth]) bfsTraversal.byDepth[depth] = [];
      bfsTraversal.byDepth[depth].push(id);
      for (const next of adj.get(id) || []) {
        if (!visited.has(next)) {
          visited.add(next);
          bfsTraversal.depthMap[next] = depth + 1;
          queue.push({ id: next, depth: depth + 1 });
        }
      }
    }
  }

  // --- E. Non-code file inventory ---
  const nonCodeFiles = {
    documentation: [],
    infrastructure: [],
    data: [],
    config: []
  };
  for (const n of nodes) {
    const entry = { id: n.id, name: n.name, type: n.type, summary: n.summary };
    if (n.type === 'document') nonCodeFiles.documentation.push(entry);
    else if (['service', 'pipeline', 'resource'].includes(n.type)) nonCodeFiles.infrastructure.push(entry);
    else if (['table', 'schema', 'endpoint'].includes(n.type)) nonCodeFiles.data.push(entry);
    else if (n.type === 'config') nonCodeFiles.config.push(entry);
  }

  // --- F. Tightly coupled clusters ---
  // bidirectional pairs on imports/calls
  const directed = new Map(); // "src|tgt" -> type
  for (const e of edges) {
    if (e.type === 'imports' || e.type === 'calls' || e.type === 'depends_on') {
      directed.set(`${e.source}|${e.target}`, e.type);
    }
  }
  const bidirPairs = [];
  for (const [key] of directed) {
    const [a, b] = key.split('|');
    if (directed.has(`${b}|${a}`) && a !== b) {
      bidirPairs.push([a, b].sort());
    }
  }
  // dedupe pairs
  const seenPair = new Set();
  const uniquePairs = [];
  for (const p of bidirPairs) {
    const k = p.join('|');
    if (!seenPair.has(k)) { seenPair.add(k); uniquePairs.push(p); }
  }

  // union-find style clustering: start from each pair, expand by adding nodes connected to 2+ members
  function edgeCountAmong(set) {
    let c = 0;
    for (const e of edges) {
      if (e.type === 'imports' || e.type === 'calls' || e.type === 'depends_on') {
        if (set.has(e.source) && set.has(e.target)) c++;
      }
    }
    return c;
  }

  // build neighbor sets for expansion
  const neighbors = new Map();
  for (const n of nodes) neighbors.set(n.id, new Set());
  for (const e of edges) {
    if (e.type === 'imports' || e.type === 'calls' || e.type === 'depends_on') {
      if (neighbors.has(e.source)) neighbors.get(e.source).add(e.target);
      if (neighbors.has(e.target)) neighbors.get(e.target).add(e.source);
    }
  }

  const clusters = [];
  const usedInCluster = new Set();
  for (const [a, b] of uniquePairs) {
    if (usedInCluster.has(a) && usedInCluster.has(b)) continue;
    const members = new Set([a, b]);
    // expand: add nodes that connect to 2+ members
    let changed = true;
    while (changed && members.size < 5) {
      changed = false;
      for (const m of Array.from(members)) {
        for (const nb of (neighbors.get(m) || [])) {
          if (members.has(nb)) continue;
          // count connections to existing members
          let conn = 0;
          for (const mm of members) {
            if ((neighbors.get(nb) || []).has(mm)) conn++;
          }
          if (conn >= 2) {
            members.add(nb);
            changed = true;
            if (members.size >= 5) break;
          }
        }
        if (members.size >= 5) break;
      }
    }
    const memberArr = Array.from(members);
    for (const m of memberArr) usedInCluster.add(m);
    clusters.push({ nodes: memberArr, edgeCount: edgeCountAmong(members) });
  }
  clusters.sort((a, b) => b.edgeCount - a.edgeCount);
  const topClusters = clusters.slice(0, 10);

  // --- G. Layer list ---
  const layerOut = {
    count: layers.length,
    list: layers.map(l => ({ id: l.id, name: l.name, description: l.description }))
  };

  // --- H. Node summary index ---
  const nodeSummaryIndex = {};
  for (const n of nodes) {
    nodeSummaryIndex[n.id] = { name: n.name, type: n.type, summary: n.summary };
  }

  const result = {
    scriptCompleted: true,
    entryPointCandidates,
    fanInRanking,
    fanOutRanking,
    bfsTraversal,
    nonCodeFiles,
    clusters: topClusters,
    layers: layerOut,
    nodeSummaryIndex,
    totalNodes: nodes.length,
    totalEdges: edges.length
  };

  fs.writeFileSync(outPath, JSON.stringify(result, null, 2));
  console.log('Analysis complete. Wrote', outPath);
  console.log('  nodes:', nodes.length, 'edges:', edges.length);
  console.log('  entry candidates:', entryPointCandidates.length);
  console.log('  bfs reached:', bfsTraversal.order.length, 'nodes from', startNode);
  console.log('  clusters:', topClusters.length);
}

try {
  main();
  process.exit(0);
} catch (err) {
  console.error('FATAL:', err && err.stack ? err.stack : err);
  process.exit(1);
}
