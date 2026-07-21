#!/usr/bin/env node
/**
 * Architecture Analyzer - Phase 1 structural analysis.
 *
 * Usage: node ua-arch-analyze.js <input.json> <output.json>
 */
'use strict';

const fs = require('fs');

function fail(msg) {
  process.stderr.write('ERROR: ' + msg + '\n');
  process.exit(1);
}

const [, , inputPath, outputPath] = process.argv;
if (!inputPath || !outputPath) {
  fail('Usage: node ua-arch-analyze.js <input.json> <output.json>');
}

let data;
try {
  data = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
} catch (e) {
  fail('Could not read/parse input: ' + e.message);
}

const fileNodes = Array.isArray(data.fileNodes) ? data.fileNodes : [];
const importEdges = Array.isArray(data.importEdges) ? data.importEdges : [];
const allEdges = Array.isArray(data.allEdges) ? data.allEdges : [];

// Normalize forward slashes
function norm(p) {
  return (p || '').replace(/\\/g, '/');
}

// Build id -> node map
const nodeById = new Map();
for (const n of fileNodes) nodeById.set(n.id, n);

// --- A. Directory Grouping ---
// Compute common path prefix (directory-wise) across all filePaths.
function pathSegments(p) {
  p = norm(p);
  // strip leading "./"
  if (p.startsWith('./')) p = p.slice(2);
  return p.split('/').filter(Boolean);
}

const allSegs = fileNodes.map(n => pathSegments(n.filePath));
// Common prefix = shared leading segments across ALL files.
let prefixLen = 0;
if (allSegs.length > 0) {
  const minLen = Math.min(...allSegs.map(s => s.length));
  outer: for (let i = 0; i < minLen; i++) {
    const seg = allSegs[0][i];
    for (let j = 1; j < allSegs.length; j++) {
      if (allSegs[j][i] !== seg) break outer;
    }
    prefixLen = i + 1;
  }
}
const commonPrefix = allSegs.length ? allSegs[0].slice(0, prefixLen).join('/') + '/' : '';

function groupKey(filePath) {
  const segs = pathSegments(filePath);
  const rest = segs.slice(prefixLen);
  if (rest.length === 0) return '(root)';
  if (rest.length === 1) {
    // file directly under common prefix - use its directory (which is root)
    return '(root)';
  }
  // Use the full remaining path joined with '/' to preserve nested grouping signal,
  // but for grouping we take the FIRST directory segment after the prefix.
  return rest[0];
}

// Flat structure detection: if there are no subdirectories after prefix, group by file pattern
const restSegs = fileNodes.map(n => pathSegments(n.filePath).slice(prefixLen));
const hasSubdirs = restSegs.some(s => s.length > 1);

const directoryGroups = {};
if (!hasSubdirs && fileNodes.length > 0) {
  // Flat structure - group by file type/extension pattern
  for (const n of fileNodes) {
    let key = 'other';
    const name = n.name || '';
    if (/\.test\./.test(name) || /\.spec\./.test(name) || /^test_/.test(name) || /_test\.go$/.test(name) || /Test\.(java|cs)$/.test(name) || /_spec\.rb$/.test(name)) key = 'test';
    else if (/\.config\./.test(name) || /\.(toml|yaml|yml|ini|env)$/.test(name)) key = 'config';
    else if (/\.(json)$/.test(name)) key = 'config';
    else if (/\.(md|rst)$/.test(name)) key = 'documentation';
    else if (/Dockerfile/.test(name) || /docker-compose/.test(name)) key = 'infrastructure';
    else if (/\.(tf|tfvars)$/.test(name)) key = 'infrastructure';
    else if (/\.(sql|graphql|gql|proto)$/.test(name)) key = 'data';
    else key = name.split('.').pop() || 'other';
    (directoryGroups[key] = directoryGroups[key] || []).push(n.id);
  }
} else {
  for (const n of fileNodes) {
    const k = groupKey(n.filePath);
    (directoryGroups[k] = directoryGroups[k] || []).push(n.id);
  }
}

// --- B. Node Type Grouping ---
const nodeTypeGroups = {};
for (const n of fileNodes) {
  const t = n.type || 'file';
  (nodeTypeGroups[t] = nodeTypeGroups[t] || []).push(n.id);
}

// --- C. Import Adjacency / Fan-In / Fan-Out ---
// Use only file-level nodes for import edges between files.
const importEdgesBetweenFiles = importEdges.filter(
  e => nodeById.has(e.source) && nodeById.has(e.target)
);

const fanOut = {};
const fanIn = {};
for (const n of fileNodes) {
  fanOut[n.id] = 0;
  fanIn[n.id] = 0;
}
for (const e of importEdgesBetweenFiles) {
  fanOut[e.source] = (fanOut[e.source] || 0) + 1;
  fanIn[e.target] = (fanIn[e.target] || 0) + 1;
}

// Group-level fan in/out
function groupOf(id) {
  for (const [k, ids] of Object.entries(directoryGroups)) {
    if (ids.includes(id)) return k;
  }
  return null;
}
const groupImportsFrom = {}; // group -> Set of groups it imports from
const groupImportsBy = {}; // group -> Set of groups importing it
for (const g of Object.keys(directoryGroups)) {
  groupImportsFrom[g] = new Set();
  groupImportsBy[g] = new Set();
}
for (const e of importEdgesBetweenFiles) {
  const sg = groupOf(e.source);
  const tg = groupOf(e.target);
  if (sg && tg && sg !== tg) {
    groupImportsFrom[sg].add(tg);
    groupImportsBy[tg].add(sg);
  }
}

// --- D. Cross-Category Dependency Analysis ---
function typeOf(id) {
  const n = nodeById.get(id);
  return n ? n.type || 'file' : null;
}
const crossCount = new Map(); // "fromType|toType|edgeType" -> count
const crossEdgesFileLevel = allEdges.filter(
  e => nodeById.has(e.source) && nodeById.has(e.target)
);
for (const e of crossEdgesFileLevel) {
  const ft = typeOf(e.source);
  const tt = typeOf(e.target);
  if (!ft || !tt) continue;
  const key = ft + '|' + tt + '|' + (e.type || 'unknown');
  crossCount.set(key, (crossCount.get(key) || 0) + 1);
}
const crossCategoryEdges = [];
for (const [key, count] of crossCount.entries()) {
  const [fromType, toType, edgeType] = key.split('|');
  crossCategoryEdges.push({ fromType, toType, edgeType, count });
}
crossCategoryEdges.sort((a, b) => b.count - a.count);

// --- E. Inter-Group Import Frequency ---
const interCounts = new Map(); // "from|to" -> count
for (const e of importEdgesBetweenFiles) {
  const sg = groupOf(e.source);
  const tg = groupOf(e.target);
  if (sg && tg && sg !== tg) {
    const key = sg + '|' + tg;
    interCounts.set(key, (interCounts.get(key) || 0) + 1);
  }
}
const interGroupImports = [];
for (const [key, count] of interCounts.entries()) {
  const [from, to] = key.split('|');
  interGroupImports.push({ from, to, count });
}
interGroupImports.sort((a, b) => b.count - a.count);

// --- F. Intra-Group Import Density ---
const intraGroupDensity = {};
for (const g of Object.keys(directoryGroups)) {
  intraGroupDensity[g] = { internalEdges: 0, totalEdges: 0, density: 0 };
}
for (const e of importEdgesBetweenFiles) {
  const sg = groupOf(e.source);
  const tg = groupOf(e.target);
  if (!sg || !tg) continue;
  if (sg === tg) {
    intraGroupDensity[sg].internalEdges += 1;
    intraGroupDensity[sg].totalEdges += 1;
  } else {
    intraGroupDensity[sg].totalEdges += 1;
    intraGroupDensity[tg].totalEdges += 1;
  }
}
for (const g of Object.keys(intraGroupDensity)) {
  const d = intraGroupDensity[g];
  d.density = d.totalEdges > 0 ? +(d.internalEdges / d.totalEdges).toFixed(3) : 0;
}

// --- G. Directory Pattern Matching ---
const dirPatterns = [
  [/^(routes|api|controllers|endpoints|handlers|routers|controller|blueprints|serializers)$/, 'api'],
  [/^(services|core|lib|domain|logic|internal|signals|composables|mailers|jobs|channels)$/, 'service'],
  [/^(models|db|data|persistence|repository|entities|entity|migrations|sql|database|schema)$/, 'data'],
  [/^(components|views|pages|ui|layouts|screens)$/, 'ui'],
  [/^(middleware|plugins|interceptors|guards)$/, 'middleware'],
  [/^(utils|helpers|common|shared|tools|templatetags|pkg)$/, 'utility'],
  [/^(config|constants|env|settings|management|commands)$/, 'config'],
  [/^(__tests__|test|tests|spec|specs)$/, 'test'],
  [/^(types|interfaces|schemas|contracts|dtos|dto|request|response)$/, 'types'],
  [/^hooks$/, 'hooks'],
  [/^(store|state|reducers|actions|slices)$/, 'state'],
  [/^(assets|static|public)$/, 'assets'],
  [/^cmd$/, 'entry'],
  [/^bin$/, 'entry'],
  [/^(docs|documentation|wiki)$/, 'documentation'],
  [/^(deploy|deployment|infra|infrastructure|k8s|kubernetes|helm|charts|terraform|tf|docker)$/, 'infrastructure'],
  [/^(\.github|\.gitlab|\.circleci)$/, 'ci-cd'],
];

function fileLevelPattern(filePath, name) {
  const p = norm(filePath);
  const n = name || '';
  if (/\.test\./.test(n) || /\.spec\./.test(n) || /^test_.*\.py$/.test(n) || /_test\.go$/.test(n) || /Test\.(java|cs)$/.test(n) || /_spec\.rb$/.test(n) || /Test\.php$/.test(n) || /Tests\.cs$/.test(n)) return 'test';
  if (/\.d\.ts$/.test(n)) return 'types';
  if (/^(index\.ts|index\.js|__init__\.py)$/.test(n)) return 'entry';
  if (n === 'manage.py') return 'entry';
  if (n === 'wsgi.py' || n === 'asgi.py') return 'config';
  if (/^cmd\/[^/]+\/main\.go$/.test(p)) return 'entry';
  if (n === 'main.rs' || n === 'lib.rs') return 'entry';
  if (n === 'Application.java' || n === 'Program.cs') return 'entry';
  if (n === 'config.ru') return 'entry';
  if (n === 'Cargo.toml' || n === 'go.mod' || n === 'Gemfile' || n === 'pom.xml' || n === 'build.gradle' || n === 'composer.json') return 'config';
  if (/^Dockerfile/.test(n) || /^docker-compose/.test(n)) return 'infrastructure';
  if (/\.tf$/.test(n) || /\.tfvars$/.test(n)) return 'infrastructure';
  if (/^\.github\/workflows\//.test(p) || n === '.gitlab-ci.yml' || n === 'Jenkinsfile') return 'ci-cd';
  if (/\.sql$/.test(n)) return 'data';
  if (/\.graphql$/.test(n) || /\.gql$/.test(n) || /\.proto$/.test(n)) return 'types';
  if (/\.md$/.test(n) || /\.rst$/.test(n)) return 'documentation';
  if (n === 'Makefile') return 'infrastructure';
  return null;
}

const patternMatches = {};
for (const g of Object.keys(directoryGroups)) {
  // First, try matching the group name itself
  let matched = null;
  for (const [re, label] of dirPatterns) {
    if (re.test(g)) { matched = label; break; }
  }
  // Special cases for nested prefixes mentioned in the prompt
  if (!matched) {
    if (g === 'src/main/java') matched = 'service';
    else if (g === 'src/test/java') matched = 'test';
  }
  patternMatches[g] = matched;

  // Also compute file-level patterns for members to inform ambiguous cases
  const memberPatterns = {};
  for (const id of directoryGroups[g]) {
    const n = nodeById.get(id);
    if (!n) continue;
    const fp = fileLevelPattern(n.filePath, n.name);
    if (fp) memberPatterns[fp] = (memberPatterns[fp] || 0) + 1;
  }
  // If group pattern is null, derive from dominant member file pattern
  if (!matched) {
    let best = null, bestCount = 0;
    for (const [k, v] of Object.entries(memberPatterns)) {
      if (v > bestCount) { best = k; bestCount = v; }
    }
    if (best) patternMatches[g] = best;
  }
}

// --- H. Deployment Topology Detection ---
const infraFiles = [];
let hasDockerfile = false, hasCompose = false, hasK8s = false, hasTerraform = false, hasCI = false;
for (const n of fileNodes) {
  const p = norm(n.filePath);
  const nm = n.name || '';
  if (/^Dockerfile/.test(nm) || /^docker-compose/.test(nm)) {
    infraFiles.push(p);
    if (/^Dockerfile/.test(nm)) hasDockerfile = true;
    if (/^docker-compose/.test(nm)) hasCompose = true;
  }
  if (/\.(tf|tfvars)$/.test(nm)) { infraFiles.push(p); hasTerraform = true; }
  if (/\.(yaml|yml)$/.test(nm) && /(^|\/)(k8s|kubernetes|helm|charts)\//.test(p)) { infraFiles.push(p); hasK8s = true; }
  if (/^\.github\/workflows\//.test(p) || nm === '.gitlab-ci.yml' || nm === 'Jenkinsfile') {
    infraFiles.push(p); hasCI = true;
  }
  if (n.type === 'service' || n.type === 'resource') infraFiles.push(p);
}
const deploymentTopology = {
  hasDockerfile, hasCompose, hasK8s, hasTerraform, hasCI,
  infraFiles: Array.from(new Set(infraFiles)),
};

// --- I. Data Pipeline Detection ---
const schemaFiles = [], migrationFiles = [], dataModelFiles = [], apiHandlerFiles = [];
for (const n of fileNodes) {
  const p = norm(n.filePath);
  const nm = n.name || '';
  if (/\.sql$/.test(nm) || /\.graphql$/.test(nm) || /\.gql$/.test(nm) || /\.proto$/.test(nm) || /\.prisma$/.test(nm)) schemaFiles.push(p);
  if (/(^|\/)migrations?\//.test(p) && /\.sql$/.test(nm)) migrationFiles.push(p);
  if (n.type === 'table' || n.type === 'schema' || n.type === 'endpoint') dataModelFiles.push(p);
  if (/(^|\/)(models|entities|repository)\//.test(p)) dataModelFiles.push(p);
  if (/(^|\/)(routes|api|controllers|endpoints|handlers)\//.test(p)) apiHandlerFiles.push(p);
}

const dataPipeline = {
  schemaFiles: Array.from(new Set(schemaFiles)),
  migrationFiles: Array.from(new Set(migrationFiles)),
  dataModelFiles: Array.from(new Set(dataModelFiles)),
  apiHandlerFiles: Array.from(new Set(apiHandlerFiles)),
};

// --- J. Documentation Coverage ---
const groupsWithDocs = [];
for (const g of Object.keys(directoryGroups)) {
  const hasDoc = directoryGroups[g].some(id => {
    const n = nodeById.get(id);
    return n && (n.type === 'document' || /\.(md|rst)$/.test(n.name || ''));
  });
  if (hasDoc) groupsWithDocs.push(g);
}
const totalGroups = Object.keys(directoryGroups).length;
const undocumentedGroups = Object.keys(directoryGroups).filter(g => !groupsWithDocs.includes(g));
const docCoverage = {
  groupsWithDocs: groupsWithDocs.length,
  totalGroups,
  coverageRatio: totalGroups ? +(groupsWithDocs.length / totalGroups).toFixed(2) : 0,
  undocumentedGroups,
};

// --- K. Dependency Direction ---
const pairDir = new Map(); // "A|B" -> net count (A->B positive)
for (const e of importEdgesBetweenFiles) {
  const sg = groupOf(e.source);
  const tg = groupOf(e.target);
  if (!sg || !tg || sg === tg) continue;
  const k = sg + '|' + tg;
  pairDir.set(k, (pairDir.get(k) || 0) + 1);
}
const dependencyDirection = [];
for (const [key, cnt] of pairDir.entries()) {
  const [a, b] = key.split('|');
  const reverse = b + '|' + a;
  const reverseCnt = pairDir.get(reverse) || 0;
  if (cnt > reverseCnt) {
    dependencyDirection.push({ dependent: a, dependsOn: b, netCount: cnt - reverseCnt });
  } else if (reverseCnt > cnt) {
    // will be added when iterating reverse key; skip to avoid duplicate
  } else if (cnt > 0 && reverseCnt === cnt) {
    // bidirectional tie - record one direction with net 0
    if (!dependencyDirection.find(d => (d.dependent === a && d.dependsOn === b) || (d.dependent === b && d.dependsOn === a))) {
      dependencyDirection.push({ dependent: a, dependsOn: b, netCount: 0 });
    }
  }
}
dependencyDirection.sort((a, b) => b.netCount - a.netCount);

// --- File stats ---
const filesPerGroup = {};
for (const g of Object.keys(directoryGroups)) filesPerGroup[g] = directoryGroups[g].length;
const nodeTypeCounts = {};
for (const t of Object.keys(nodeTypeGroups)) nodeTypeCounts[t] = nodeTypeGroups[t].length;

const fileStats = {
  totalFileNodes: fileNodes.length,
  filesPerGroup,
  nodeTypeCounts,
};

// Fan maps - sort for readability, keep all entries
const fileFanIn = {};
const fileFanOut = {};
for (const n of fileNodes) {
  fileFanIn[n.id] = fanIn[n.id] || 0;
  fileFanOut[n.id] = fanOut[n.id] || 0;
}

const result = {
  scriptCompleted: true,
  commonPrefix,
  directoryGroups,
  nodeTypeGroups,
  crossCategoryEdges,
  interGroupImports,
  intraGroupDensity,
  patternMatches,
  deploymentTopology,
  dataPipeline,
  docCoverage,
  dependencyDirection,
  fileStats,
  fileFanIn,
  fileFanOut,
};

try {
  fs.writeFileSync(outputPath, JSON.stringify(result, null, 2));
  process.exit(0);
} catch (e) {
  fail('Could not write output: ' + e.message);
}
