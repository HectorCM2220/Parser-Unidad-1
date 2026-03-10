const svg = document.getElementById('tree-svg');
const linksGroup = document.getElementById('links-group');
const nodesGroup = document.getElementById('nodes-group');
const codigoInput = document.getElementById('codigo-fuente');
const analizarBtn = document.getElementById('analizar-btn');
const statusBubble = document.getElementById('status-bubble');

let treeData = null;
const NODE_RADIUS = 35;
const VERTICAL_SPACING = 120;

async function analizar() {
    const codigo = codigoInput.value.trim();
    if (!codigo) return;

    const response = await fetch('/analizar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ codigo })
    });

    if (response.ok) {
        treeData = await response.json();
        renderTree();
        showStatus("Árbol generado");
    } else {
        const error = await response.json();
        showStatus(error.detail || "Error al analizar", true);
    }
}

function renderTree() {
    linksGroup.innerHTML = '';
    nodesGroup.innerHTML = '';
    if (!treeData) return;

    const width = svg.clientWidth || window.innerWidth - 320;
    calculatePositions(treeData, width / 2, 60, width / 2);
    drawTree(treeData);
}

function calculatePositions(node, x, y, horizontalRange) {
    if (!node) return;
    node.x = x;
    node.y = y;

    if (node.hijos && node.hijos.length > 0) {
        const n = node.hijos.length;
        const startX = x - horizontalRange / 2;
        const step = n > 1 ? horizontalRange / (n - 1) : 0;
        const nextRange = horizontalRange / 2;

        node.hijos.forEach((hijo, i) => {
            const hijoX = n > 1 ? startX + i * step : x;
            calculatePositions(hijo, hijoX, y + VERTICAL_SPACING, nextRange);
        });
    }
}

function drawTree(node) {
    if (!node) return;

    if (node.hijos) {
        node.hijos.forEach(hijo => {
            const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
            line.setAttribute("x1", node.x);
            line.setAttribute("y1", node.y);
            line.setAttribute("x2", hijo.x);
            line.setAttribute("y2", hijo.y);
            line.classList.add("node-link");
            linksGroup.appendChild(line);
            drawTree(hijo);
        });
    }

    const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    group.classList.add("node-element");

    const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
    title.textContent = node.valor;
    group.appendChild(title);

    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", node.x);
    circle.setAttribute("cy", node.y);
    circle.setAttribute("r", NODE_RADIUS);
    circle.classList.add("node-circle");

    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", node.x);
    text.setAttribute("y", node.y);
    const displayValue = node.valor.length > 10 ? node.valor.substring(0, 8) + ".." : node.valor;
    text.textContent = displayValue;
    text.classList.add("node-text");

    group.appendChild(circle);
    group.appendChild(text);
    nodesGroup.appendChild(group);
}

function showStatus(text, isError = false) {
    statusBubble.textContent = text;
    statusBubble.classList.remove('hidden', 'error');
    if (isError) statusBubble.classList.add('error');
    setTimeout(() => statusBubble.classList.add('hidden'), 4000);
}

analizarBtn.addEventListener('click', analizar);
window.addEventListener('resize', renderTree);
