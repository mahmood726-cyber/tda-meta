document.addEventListener('DOMContentLoaded', () => {
    const btnCompute = document.getElementById('btnCompute');
    const ctx = document.getElementById('voidChart').getContext('2d');
    
    const voidChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{ 
                label: 'Topological Isolation Score (Persistence)', 
                data: [], 
                backgroundColor: [], 
                barThickness: 20 
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } },
                x: { grid: { color: '#1e293b' }, ticks: { color: '#f8fafc' } }
            },
            plugins: {
                legend: { display: false },
                title: { display: true, text: 'Evidence Voids Ranked by Persistent Homology', color: '#94a3b8' }
            }
        }
    });

    btnCompute.addEventListener('click', async () => {
        btnCompute.disabled = true;
        btnCompute.textContent = 'Scanning Topology...';
        
        try {
            const resp = await fetch('data/tda_results.json');
            const result = await resp.json();
            const gaps = result.evidence_gaps;
            
            // Filter to show actual gaps (exclude the "connected component" that lives forever)
            const validGaps = gaps.filter(g => g.isolation_score < 9999);
            
            // Colors: red for extreme voids, yellow for moderate
            const colors = validGaps.map(g => g.isolation_score_normalized > 70 ? '#ef4444' : '#facc15');

            // Update Chart
            voidChart.data.labels = validGaps.map(d => d.domain);
            voidChart.data.datasets[0].data = validGaps.map(d => d.isolation_score_normalized);
            voidChart.data.datasets[0].backgroundColor = colors;
            voidChart.update();
            
            // Update Metrics
            document.getElementById('domainCount').textContent = result.domains.length;
            const extremes = validGaps.filter(g => g.isolation_score_normalized > 70).length;
            document.getElementById('voidCount').textContent = extremes;
            document.getElementById('voidCount').style.color = extremes > 0 ? '#ef4444' : '#f8fafc';
            
            // Update Details
            const detailsDiv = document.getElementById('gapDetails');
            detailsDiv.innerHTML = validGaps.map(g => `
                <div class="gap-card ${g.isolation_score_normalized > 70 ? 'critical' : ''}">
                    <h3>${g.domain}</h3>
                    <p>Isolation (0-100): <span class="gap-score">${g.isolation_score_normalized.toFixed(1)}</span></p>
                    <p>Raw Persistence: ${g.isolation_score.toFixed(2)}</p>
                    ${g.isolation_score_normalized > 70 ? '<p style="color:#ef4444; font-size:0.8rem; margin-top:0.5rem;">CRITICAL EVIDENCE VOID</p>' : ''}
                </div>
            `).join('');
            
        } catch (e) {
            console.error('Failed to load TDA data:', e);
        } finally {
            btnCompute.textContent = 'Scan Topology';
            btnCompute.disabled = false;
        }
    });

    // Auto-load if data exists
    btnCompute.click();
});
