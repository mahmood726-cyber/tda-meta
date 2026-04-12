document.addEventListener('DOMContentLoaded', () => {
    const btnCompute = document.getElementById('btnCompute');
    const chartRoot = document.getElementById('voidChart');
    const statusBanner = document.getElementById('statusBanner');
    const auditStamp = document.getElementById('auditStamp');
    const detailsDiv = document.getElementById('gapDetails');

    function getEmbeddedPayload() {
        if (window.__TDA_DATA__ && Array.isArray(window.__TDA_DATA__.evidence_gaps)) {
            return window.__TDA_DATA__;
        }

        return null;
    }

    function setStatus(message, tone = 'info') {
        statusBanner.textContent = message;
        statusBanner.dataset.tone = tone;
    }

    function renderAudit(audit) {
        const methodStamp = document.getElementById('methodologyStamp');
        if (!audit || !audit.timestamp) {
            auditStamp.textContent = 'Audit stamp unavailable.';
            methodStamp.textContent = 'Methodology: Pending...';
            return;
        }

        auditStamp.textContent = `Audit: ${new Date(audit.timestamp).toLocaleString()}`;
        methodStamp.textContent = `Method: ${audit.methodology || 'E156 Standard'}`;
    }

    function renderChart(validGaps) {
        const maxValue = Math.max(1, ...validGaps.map((gap) => Number(gap.isolation_score_normalized)));
        const rows = validGaps.map((gap) => {
            const row = document.createElement('div');
            const label = document.createElement('div');
            const track = document.createElement('div');

            row.className = 'bar-row';
            label.className = 'bar-label';
            label.textContent = gap.domain;

            const iso = Number(gap.isolation_score_normalized);
            const range = gap.conformal_range || [iso, iso];
            const lowerPerc = (range[0] / gap.isolation_score) * iso;
            const upperPerc = (range[1] / gap.isolation_score) * iso;
            const rangeWidth = ((upperPerc - lowerPerc) / maxValue) * 100;
            const rangeLeft = (lowerPerc / maxValue) * 100;

            track.className = `bar-track ${gap.is_anomalous ? 'critical' : 'moderate'}`;
            track.innerHTML = `
                <span class="bar-fill" style="width: ${(iso / maxValue) * 100}%"></span>
                <span class="conformal-interval" style="left: ${rangeLeft}%; width: ${rangeWidth}%"></span>
                <span class="bar-value">${iso.toFixed(1)}</span>
            `;

            row.append(label, track);
            return row;
        });

        chartRoot.replaceChildren(...rows);
    }

    function renderEmptyState(message, tone = 'info') {
        const node = document.createElement('div');
        node.className = `empty-state ${tone}`;
        node.textContent = message;
        detailsDiv.replaceChildren(node);
        chartRoot.replaceChildren(node.cloneNode(true));
    }

    async function loadResults() {
        btnCompute.disabled = true;
        btnCompute.textContent = 'Scanning Topology...';
        setStatus('Loading evidence void bundle...', 'loading');

        try {
            let result = getEmbeddedPayload();
            let sourceLabel = 'embedded JS bundle';

            if (!result) {
                sourceLabel = 'JSON artifact';
                const resp = await fetch('data/tda_results.json', { cache: 'no-store' });
                if (!resp.ok) {
                    throw new Error(`Data fetch failed with status ${resp.status}`);
                }
                result = await resp.json();
            }

            if (!result || !Array.isArray(result.evidence_gaps) || !Array.isArray(result.domains)) {
                throw new Error('The topological evidence bundle is malformed.');
            }

            const gaps = result.evidence_gaps;
            
            // Filter to show actual gaps (exclude the "connected component" that lives forever)
            const validGaps = gaps.filter(g => g.isolation_score < 9999);

            renderChart(validGaps);
            
            // Update Metrics
            document.getElementById('domainCount').textContent = result.domains.length;
            const extremes = validGaps.filter(g => g.isolation_score_normalized > 70).length;
            document.getElementById('voidCount').textContent = extremes;
            document.getElementById('voidCount').style.color = extremes > 0 ? '#ef4444' : '#f8fafc';
            
            // Render Clinical Labels in Sidebar (Informational)
            const controlsDiv = document.querySelector('.controls');
            if (!document.getElementById('manifoldLabel')) {
                const label = document.createElement('p');
                label.id = 'manifoldLabel';
                label.style.fontSize = '0.65rem';
                label.style.color = '#94a3b8';
                label.style.marginTop = '0.5rem';
                label.innerHTML = 'Manifold [7D]: [Age, %Female, N, SES, Prev, Infra, <b>Reliability</b>]';
                controlsDiv.appendChild(label);
            }
            
            // Update Details
            const detailsDiv = document.getElementById('gapDetails');
            detailsDiv.innerHTML = validGaps.map(g => {
                const isRetracted = (g.reliability_index || 1.0) < 1.0;
                return `
                <div class="gap-card ${g.is_anomalous ? 'critical anomalous' : ''} ${isRetracted ? 'retracted' : ''}">
                    <h3>${g.domain}</h3>
                    <p>Isolation (0-100): <span class="gap-score">${g.isolation_score_normalized.toFixed(1)}</span></p>
                    <p style="font-size:0.75rem; color:#64748b;">95% Conformal: [${(g.conformal_range[0]).toFixed(2)}, ${(g.conformal_range[1]).toFixed(2)}]</p>
                    <div class="truth-cert">
                        <span>Cert: ${g.truth_cert?.locator || 'UNCERTIFIED'}</span>
                        <span>Hash: ${g.truth_cert?.hash || '0x00'}</span>
                        <span style="color: ${isRetracted ? '#ef4444' : '#10b981'}; font-weight:bold;">
                            Reliability: ${(g.reliability_index * 100).toFixed(0)}% ${isRetracted ? ' (SHOCK)' : ''}
                        </span>
                    </div>
                    ${isRetracted ? '<p style="color:#ef4444; font-size:0.6rem; margin-top:0.3rem; font-weight:bold;">RELIABILITY SINK - COLLAPSED EVIDENCE</p>' : ''}
                    ${g.is_anomalous && !isRetracted ? '<p style="color:#facc15; font-size:0.65rem; margin-top:0.4rem; font-weight:bold; letter-spacing:0.05em;">DML-HARDENED ANOMALY</p>' : ''}
                </div>
                `;
            }).join('');
            renderAudit(result.audit);
            setStatus(`Loaded ${validGaps.length} ranked evidence gaps from ${sourceLabel}.`, 'success');
            
        } catch (e) {
            console.error('Failed to load TDA data:', e);
            renderAudit(null);
            renderEmptyState('Failed to load TDA evidence bundle. Run the Python pipeline first.', 'error');
            setStatus(e.message, 'error');
        } finally {
            btnCompute.textContent = 'Scan Topology';
            btnCompute.disabled = false;
        }
    }

    btnCompute.addEventListener('click', () => {
        void loadResults();
    });

    void loadResults();
});
