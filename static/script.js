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
    linksGroup.removeAttribute('transform');
    nodesGroup.removeAttribute('transform');

    if (!treeData) return;

    // Reiniciamos el contador global X para dibujar el árbol desde la izquierda
    globalLeafX = 0;

    // Calcular posiciones garantizando que ninguna hoja se superponga
    calculatePositions(treeData, 0);

    // Dibujar los elementos primero para que el navegador calcule su caja (BBox)
    drawTree(treeData);

    // Necesitamos un macro-task para que el SVG calcule el BBox correctamente en el DOM
    setTimeout(() => {
        try {
            const bbox = nodesGroup.getBBox();
            const padding = 100;

            const treeWidth = bbox.width + padding * 2;
            const treeHeight = bbox.height + bbox.y + padding;

            const containerArea = svg.parentElement;
            const containerWidth = containerArea.clientWidth;
            const containerHeight = containerArea.clientHeight;

            const finalWidth = Math.max(containerWidth, treeWidth);
            const finalHeight = Math.max(containerHeight, treeHeight);

            // Forzar el tamaño del SVG para habilitar el scroll del contenedor si excede el tamaño
            svg.setAttribute("width", finalWidth);
            svg.setAttribute("height", finalHeight);

            // Centrar el árbol horizontalmente desplazando los grupos
            const shiftX = (finalWidth / 2) - (bbox.x + bbox.width / 2);

            nodesGroup.setAttribute('transform', `translate(${shiftX}, 0)`);
            linksGroup.setAttribute('transform', `translate(${shiftX}, 0)`);

        } catch (e) {
            console.error("No se pudo calcular la caja de dimensiones", e);
        }
    }, 0);
}

const HORIZONTAL_SPACING = 100; // Espaciado estricto entre hojas
let globalLeafX = 0;

function calculatePositions(node, depth) {
    if (!node) return;

    // Altura siempre fija basada en la profundidad
    node.y = (depth * VERTICAL_SPACING) + 80;

    if (!node.hijos || node.hijos.length === 0) {
        // Es un nodo final (hoja): le damos su columna X exclusiva y avanzamos el contador
        node.x = globalLeafX;
        globalLeafX += HORIZONTAL_SPACING;
    } else {
        // Tiene hijos: calcular posiciones de todos los hijos de izquierda a derecha
        node.hijos.forEach(hijo => calculatePositions(hijo, depth + 1));

        // El padre se centra exactamente en medio de su primer y último hijo
        const firstChildX = node.hijos[0].x;
        const lastChildX = node.hijos[node.hijos.length - 1].x;
        node.x = (firstChildX + lastChildX) / 2;

        // Truco de espaciado: Si un padre no tiene hermanos pero la hoja de la derecha está lejos,
        // avanzamos ligeramente el globalLeafX para generar un respiro
        if (globalLeafX <= node.x) {
            globalLeafX = node.x + HORIZONTAL_SPACING;
        }
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
