JSON_REPLACE_HINT = r"JSON_DATA_TO_REPLACE"
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calltree Visualization with Vis.js</title>
    <style>
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
        }

        #graph-container {
            width: 100vw;
            height: 100vh;
            border: 1px solid #ccc;
            background-color: white;
        }

        .vis-network .vis-node {
            border-radius: 4px;
            padding: 5px;
            cursor: pointer;
        }

        .vis-network .vis-node.module {
            background-color: #f8f9fa;
            border: 2px solid #4a90e2;
            min-width: 200px;
            min-height: 100px;
            display: flex;
            flex-direction: column;
        }

        .vis-network .vis-node.function {
            background-color: #e6f3ff;
            border: 1px solid #4a90e2;
            margin: 5px 10px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .vis-network .vis-edge {
            color: #ff4444;
            width: 2px;
        }

        .vis-network .vis-edge:hover {
            color: #cc0000;
        }

        .vis-network .vis-arrow {
            fill: #ff4444;
        }
    </style>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
</head>

<body>
    <div id="graph-container"></div>
    <script>

        // Sample JSON data (your provided data)
        const jsonData = JSON_DATA_TO_REPLACE;

        
        
        // Create nodes and edges for Vis.js
        let nodes = new vis.DataSet();
        let edges = new vis.DataSet();
        const moduleNodes = {}; // To track module nodes for grouping

        // Group functions by module (combine .c and .h with same base name)
        jsonData.calltree.forEach(caller => {
            const filePath = caller.file;
            const baseName = filePath.split('\\').pop().split('.')[0]; // Get base name (e.g., "hello" from "hello.h" or "hello.c")

            // Ensure module node exists (combine .c and .h)
            if (!moduleNodes[baseName]) {
                const moduleId = `module_${baseName}`;
                moduleNodes[baseName] = moduleId;
                nodes.add({
                    id: moduleId,
                    label: `[M] ${baseName}`,
                    group: 'module',
                    shape: 'box',
                    color: { background: '#cce253', border: '#4a90e2', highlight: { border: '#4a90e2' } },
                    font: { size: 12, color: '#333' },
                    size: 50
                });
            }

            // Create unique ID for caller function using full file path to avoid duplicates
            const callerUniqueId = `func_${filePath.replace(/\\/g, '_').replace(/\./g, '_')}_${caller.name}`;
            if (!nodes.get(callerUniqueId)) { // Check if node already exists
                nodes.add({
                    id: callerUniqueId,
                    label: `[F] ${caller.name}`,
                    group: 'function',
                    shape: 'box',
                    color: { background: '#97dad2', border: '#4a90e2', highlight: { background: '#d1e8ff', border: '#4a90e2' } },
                    font: { size: 12 },
                    size: 50,
                    parent: moduleNodes[baseName] // Link to module
                });
            }

            // Link module to function (only if not already linked)
            if (!edges.get().some(edge => edge.from === moduleNodes[baseName] && edge.to === callerUniqueId)) {
                edges.add({ from: moduleNodes[baseName], to: callerUniqueId, arrows: 'to', color: { color: '#888888' }, smooth: true });
            }

            // Handle callees
            caller.callees.forEach(callee => {
                const calleeFilePath = callee.file;
                const calleeBaseName = calleeFilePath.split('\\').pop().split('.')[0];

                // Ensure callee module exists
                if (!moduleNodes[calleeBaseName]) {
                    const moduleId = `module_${calleeBaseName}`;
                    moduleNodes[calleeBaseName] = moduleId;
                    nodes.add({
                        id: moduleId,
                        label: `[M] ${calleeBaseName}`,
                        group: 'module',
                        shape: 'box',
                        color: { background: '#cce253', border: '#4a90e2', highlight: { border: '#4a90e2' } },
                        font: { size: 12, color: '#333' },
                        size: 50
                    });
                }

                // Create unique ID for callee function
                const calleeUniqueId = `func_${calleeFilePath.replace(/\\/g, '_').replace(/\./g, '_')}_${callee.name}`;
                if (!nodes.get(calleeUniqueId)) { // Check if node already exists
                    nodes.add({
                        id: calleeUniqueId,
                        label: `[F] ${callee.name}`,
                        group: 'function',
                        shape: 'box',
                        color: { background: '#97dad2', border: '#4a90e2', highlight: { background: '#d1e8ff', border: '#4a90e2' } },
                        font: { size: 12 },
                        size: 50,
                        parent: moduleNodes[calleeBaseName] // Link to module
                    });
                }

                // Link callee module to function (only if not already linked)
                if (!edges.get().some(edge => edge.from === moduleNodes[calleeBaseName] && edge.to === calleeUniqueId)) {
                    edges.add({ from: moduleNodes[calleeBaseName], to: calleeUniqueId, arrows: 'to', color: { color: '#888888' }, smooth: true });
                }

                // Add caller -> callee edge
                edges.add({
                    from: callerUniqueId,
                    to: calleeUniqueId,
                    arrows: 'to',
                    color: { color: '#ff4444' },
                    smooth: { type: 'curvedCW', roundness: 0.5 }, // Curved arrow
                    width: 2
                });
            });
        });

        // Create the network
        const container = document.getElementById("graph-container");
        const data = {
            nodes: nodes,
            edges: edges
        };
        const options = {
            layout: {
                hierarchical: false,
                improvedLayout: true
            },
            physics: {
                enabled: true,
                solver: 'forceAtlas2Based',
                forceAtlas2Based: {
                    gravitationalConstant: -50,
                    centralGravity: 0.01,
                    springLength: 100,
                    springConstant: 0.08
                },
                timestep: 0.35
            },
            edges: {
                smooth: { type: 'curvedCW', roundness: 0.5 }
            },
            nodes: {
                shape: 'box'
            },
            interaction: {
                zoomView: true,
                dragView: true,
                dragNodes: true
            },
            groups: {
                module: {
                    shape: 'box',
                    color: { background: '#f8f9fa', border: '#4a90e2' },
                    font: { size: 14, color: '#333' }
                },
                function: {
                    shape: 'box',
                    color: { background: '#e6f3ff', border: '#4a90e2' },
                    font: { size: 12 }
                }
            }
        };
        new vis.Network(container, data, options);



    </script>
</body>

</html>
"""