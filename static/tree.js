(() => {
  const dataElement = document.getElementById('tree-data');
  const svg = document.getElementById('search-tree');
  if (!dataElement || !svg) return;

  const root = JSON.parse(dataElement.textContent);
  const NS = 'http://www.w3.org/2000/svg';
  const cardW = 142;
  const cardH = 82;
  const gapX = 36;
  const gapY = 142;
  let leafIndex = 0;
  const nodes = [];
  const edges = [];

  function place(node, depth, parent = null, column = null) {
    const current = { node, depth, parent, column, x: 0, y: 48 + depth * gapY };
    nodes.push(current);
    if (parent) edges.push({ from: parent, to: current });
    if (!node.children || node.children.length === 0) {
      current.x = 60 + leafIndex++ * (cardW + gapX);
    } else {
      const children = node.children.map(child => place(child.node, depth + 1, current, child.column));
      current.x = (children[0].x + children[children.length - 1].x) / 2;
    }
    return current;
  }

  place(root, 0);
  const width = Math.max(700, leafIndex * (cardW + gapX) + 60);
  const height = 48 + (Math.max(...nodes.map(item => item.depth)) + 1) * gapY;
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.setAttribute('width', width);
  svg.setAttribute('height', height);

  const defs = document.createElementNS(NS, 'defs');
  const marker = document.createElementNS(NS, 'marker');
  marker.setAttribute('id', 'arrow');
  marker.setAttribute('viewBox', '0 0 10 10');
  marker.setAttribute('refX', '8');
  marker.setAttribute('refY', '5');
  marker.setAttribute('markerWidth', '7');
  marker.setAttribute('markerHeight', '7');
  marker.setAttribute('orient', 'auto-start-reverse');
  const arrow = document.createElementNS(NS, 'path');
  arrow.setAttribute('d', 'M 0 0 L 10 5 L 0 10 z');
  arrow.setAttribute('fill', '#3730AA');
  marker.appendChild(arrow);
  defs.appendChild(marker);
  svg.appendChild(defs);

  edges.forEach(({ from, to }) => {
    const path = document.createElementNS(NS, 'path');
    const x1 = from.x + cardW / 2;
    const y1 = from.y + cardH;
    const x2 = to.x + cardW / 2;
    const y2 = to.y - 3;
    const bend = (y1 + y2) / 2;
    path.setAttribute('d', `M ${x1} ${y1} C ${x1} ${bend}, ${x2} ${bend}, ${x2} ${y2}`);
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', '#3730AA');
    path.setAttribute('stroke-width', '2');
    path.setAttribute('marker-end', 'url(#arrow)');
    svg.appendChild(path);

    const label = document.createElementNS(NS, 'text');
    label.setAttribute('x', (x1 + x2) / 2);
    label.setAttribute('y', bend - 5);
    label.setAttribute('text-anchor', 'middle');
    label.setAttribute('class', 'tree-edge-label');
    label.textContent = `col ${to.column}`;
    svg.appendChild(label);
  });

  nodes.forEach(({ node, x, y }) => {
    const color = node.kind === 'MAX' ? '#3730AA' : '#FF653F';
    const group = document.createElementNS(NS, 'g');
    group.setAttribute('transform', `translate(${x},${y})`);
    group.setAttribute('class', 'tree-node');
    group.setAttribute('tabindex', '0');
    group.setAttribute('role', 'button');
    group.setAttribute('aria-label', `${node.kind} node, value ${node.value}${node.pruned ? `, pruned ${node.pruned} branches` : ''}`);
    const title = document.createElementNS(NS, 'title');
    title.textContent = `Click to inspect ${node.kind} node — value ${node.value}`;
    group.appendChild(title);

    const shadow = document.createElementNS(NS, 'rect');
    shadow.setAttribute('x', '4'); shadow.setAttribute('y', '5');
    shadow.setAttribute('width', cardW); shadow.setAttribute('height', cardH);
    shadow.setAttribute('rx', '15'); shadow.setAttribute('fill', '#16115E');
    group.appendChild(shadow);

    const card = document.createElementNS(NS, 'rect');
    card.setAttribute('width', cardW); card.setAttribute('height', cardH);
    card.setAttribute('rx', '15'); card.setAttribute('fill', '#FFFAF2');
    card.setAttribute('stroke', color); card.setAttribute('stroke-width', '3');
    group.appendChild(card);

    const badge = document.createElementNS(NS, 'rect');
    badge.setAttribute('x', '8'); badge.setAttribute('y', '8');
    badge.setAttribute('width', '65'); badge.setAttribute('height', '23');
    badge.setAttribute('rx', '9'); badge.setAttribute('fill', color);
    group.appendChild(badge);

    const role = document.createElementNS(NS, 'text');
    role.setAttribute('x', '40'); role.setAttribute('y', '24');
    role.setAttribute('text-anchor', 'middle'); role.setAttribute('class', 'tree-role');
    role.textContent = node.kind === 'MAX' ? 'AI / MAX' : node.kind === 'MIN' ? 'YOU / MIN' : 'LEAF';
    group.appendChild(role);

    const value = document.createElementNS(NS, 'text');
    value.setAttribute('x', '10'); value.setAttribute('y', '51');
    value.setAttribute('class', 'tree-value'); value.textContent = `value ${node.value ?? '—'}`;
    group.appendChild(value);

    const info = document.createElementNS(NS, 'text');
    info.setAttribute('x', '10'); info.setAttribute('y', '70');
    info.setAttribute('class', 'tree-info');
    info.textContent = node.pruned
      ? `CUT: ${node.pruned} branch${node.pruned === 1 ? '' : 'es'}`
      : node.leaf_kind ? `${node.leaf_kind} leaf` : `α ${node.alpha}   β ${node.beta}`;
    if (node.pruned) group.classList.add('tree-pruned');
    group.appendChild(info);
    group.addEventListener('click', () => inspectNode(node, group));
    group.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        inspectNode(node, group);
      }
    });
    svg.appendChild(group);
  });

  let selectedGroup = null;
  function inspectNode(node, group = null) {
    if (selectedGroup) selectedGroup.classList.remove('selected');
    selectedGroup = group;
    if (selectedGroup) selectedGroup.classList.add('selected');
    const inspector = document.getElementById('node-inspector');
    inspector.replaceChildren();

    const heading = document.createElement('h3');
    heading.textContent = `${node.kind === 'MAX' ? 'AI / MAX' : node.kind === 'MIN' ? 'YOU / MIN' : 'LEAF'} node`;
    inspector.appendChild(heading);

    const value = document.createElement('p');
    const kind = node.leaf_kind === 'HEURISTIC' ? 'Heuristic evaluation' :
      node.leaf_kind === 'TERMINAL' ? 'Exact terminal score' : 'Minimax value';
    value.textContent = `${kind}: ${node.value}; alpha: ${node.alpha}; beta: ${node.beta}`;
    inspector.appendChild(value);

    const note = document.createElement('p');
    note.className = 'inspector-note';
    note.textContent = 'Board shown from the AI search perspective: AI = X, human = O.';
    inspector.appendChild(note);

    const grid = document.createElement('div');
    grid.className = 'inspect-board';
    grid.style.setProperty('--board-cols', node.board[0].length);
    node.board.forEach(row => row.forEach(cell => {
      const slot = document.createElement('span');
      slot.className = `inspect-slot ${cell === 'FIRST' ? 'inspect-ai' : cell === 'SECOND' ? 'inspect-human' : ''}`;
      slot.textContent = cell === 'FIRST' ? 'X' : cell === 'SECOND' ? 'O' : '';
      grid.appendChild(slot);
    }));
    inspector.appendChild(grid);
  }

  inspectNode(root);
})();
