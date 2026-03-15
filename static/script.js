document.addEventListener('DOMContentLoaded', () => {
    const runBtn = document.getElementById('runBtn');
    const promptInput = document.getElementById('promptInput');
    const pipelineViz = document.getElementById('pipelineViz');
    const outputSection = document.getElementById('outputSection');
    const terminalOutput = document.getElementById('terminalOutput');
    const layers = document.querySelectorAll('.layer');

    runBtn.addEventListener('click', async () => {
        const prompt = promptInput.value.trim();
        if (!prompt) return;

        // Reset UI
        runBtn.disabled = true;
        pipelineViz.style.display = 'block';
        outputSection.style.display = 'block';
        terminalOutput.innerHTML = '> Initializing safety check...';
        layers.forEach(l => l.classList.remove('active', 'success', 'blocked'));

        try {
            // Simulated sequence animation
            await animateLayers(prompt);
            
            const response = await fetch('/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: prompt })
            });

            const result = await response.json();
            displayResult(result);

        } catch (error) {
            terminalOutput.innerHTML += `<br><span style="color:red">System Error: ${error.message}</span>`;
        } finally {
            runBtn.disabled = false;
        }
    });

    async function animateLayers(prompt) {
        const sleep = m => new Promise(r => setTimeout(r, m));
        
        for (let i = 0; i < layers.length; i++) {
            layers[i].classList.add('active');
            terminalOutput.innerHTML += `<br>> Processing Layer ${i+1}...`;
            await sleep(400);
        }
    }

    function displayResult(result) {
        const isSafe = result.success;
        const risk = result.risk || 'UNKNOWN';
        
        // Finalize layers based on result
        layers.forEach((l, i) => {
            if (isSafe) {
                l.classList.add('success');
            } else {
                // Approximate which layer blocked it for viz
                if (result.error.includes('injection') && i === 0) l.classList.add('blocked');
                else if (result.error.includes('parse') && i === 1) l.classList.add('blocked');
                else if (result.error.includes('Schema') && i === 2) l.classList.add('blocked');
                else if (result.error.includes('Safe') && i === 3) l.classList.add('blocked');
                else l.classList.add('success');
            }
        });

        if (!isSafe && !document.querySelector('.layer.blocked')) {
            layers[layers.length-1].classList.add('blocked');
        }

        let html = `<br>--- ANALYSIS COMPLETE ---<br>`;
        html += `STATUS: ${isSafe ? '<span style="color:#00f089">APPROVED</span>' : '<span style="color:#ff4d4d">BLOCKED</span>'}<br>`;
        html += `RISK LEVEL: ${risk}<br>`;
        
        if (!isSafe) {
            html += `REASON: ${result.error}<br>`;
        } else {
            html += `COMMAND: ${JSON.stringify(result.command)}<br>`;
            html += `RESULT: ${JSON.stringify(result.result)}<br>`;
        }
        
        terminalOutput.innerHTML += html;
    }
});
