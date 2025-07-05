class FraudDashboard {
    constructor() {
        this.updateInterval = null;
        this.init();
    }

    init() {
        console.log('🕵️ Fraud Hunter Dashboard Loaded');
        this.setupEventListeners();
        this.startRealTimeUpdates();
        this.setupFormHandlers();
        this.showToast('🕵️ Fraud Hunter is online!', 'info');
    }

    startRealTimeUpdates() {
        this.updateInterval = setInterval(() => {
            this.updateDashboard();
        }, 5000); // Update every 5 seconds
    }

    async updateDashboard() {
        try {
            await Promise.all([
                this.updateStats(),
                this.updateAgentsList(),
                this.updateAnalyses()
            ]);
        } catch (error) {
            console.error('Dashboard update failed:', error);
        }
    }

    async updateStats() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            this.updateElement('#running-agents-count', data.running_agents);
            this.updateElement('#total-agents-count', data.agents);
            
        } catch (error) {
            console.error('Failed to update stats:', error);
        }
    }

    updateElement(selector, newValue) {
        const element = document.querySelector(selector);
        if (element && element.textContent != newValue) {
            element.style.transform = 'scale(1.2)';
            element.style.color = '#28a745';
            element.textContent = newValue;
            
            setTimeout(() => {
                element.style.transform = 'scale(1)';
                element.style.color = '';
            }, 300);
        }
    }

    async updateAgentsList() {
        try {
            const response = await fetch('/api/agents');
            const agents = await response.json();
            
            const agentsContainer = document.querySelector('#agents-list');
            if (agentsContainer) {
                agentsContainer.innerHTML = this.renderAgents(agents);
                this.setupAgentButtons();
            }
        } catch (error) {
            console.error('Failed to update agents:', error);
        }
    }

    async updateAnalyses() {
        try {
            const response = await fetch('/api/analyses');
            const analyses = await response.json();
            
            const analysesContainer = document.querySelector('#analyses-list');
            if (analysesContainer) {
                analysesContainer.innerHTML = this.renderAnalyses(analyses);
            }
            
            const highRiskCount = analyses.filter(a => a.risk_score > 0.7).length;
            this.updateElement('#high-risk-count', highRiskCount);
            
        } catch (error) {
            console.error('Failed to update analyses:', error);
        }
    }

    renderAgents(agents) {
        return agents.map(agent => `
            <div class="d-flex justify-content-between align-items-center border-bottom py-2 agent-item" data-agent-id="${agent.agent_id}">
                <div>
                    <strong>${agent.name}</strong>
                    <br>
                    <small class="text-muted">
                        Events: ${agent.events_processed} | Alerts: ${agent.alerts_generated}
                    </small>
                </div>
                <div>
                    <span class="badge bg-${agent.status === 'running' ? 'success' : 'secondary'}">
                        ${agent.status.charAt(0).toUpperCase() + agent.status.slice(1)}
                    </span>
                    <div class="btn-group btn-group-sm mt-1">
                        ${agent.status === 'running' ? 
                            `<button class="btn btn-warning btn-sm stop-agent-btn" data-agent-id="${agent.agent_id}">⏹️ Stop</button>` :
                            `<button class="btn btn-success btn-sm start-agent-btn" data-agent-id="${agent.agent_id}">▶️ Start</button>`
                        }
                        <button class="btn btn-danger btn-sm delete-agent-btn" data-agent-id="${agent.agent_id}">🗑️</button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderAnalyses(analyses) {
        return analyses.map(analysis => `
            <div class="border-bottom py-2 analysis-item">
                <div class="d-flex justify-content-between">
                    <div>
                        <strong>${analysis.event_id}</strong>
                        <span class="badge bg-${analysis.risk_score > 0.7 ? 'danger' : analysis.risk_score > 0.5 ? 'warning' : 'success'}">
                            ${analysis.risk_score.toFixed(2)}
                        </span>
                    </div>
                    <small class="text-muted">${new Date(analysis.timestamp).toLocaleTimeString()}</small>
                </div>
                <small class="text-muted">${analysis.reasoning.substring(0, 60)}...</small>
                <br>
                <small><strong>Actions:</strong> ${analysis.recommended_actions.join(', ')}</small>
            </div>
        `).join('');
    }

    setupAgentButtons() {
        document.querySelectorAll('.start-agent-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                await this.startAgent(e.target.dataset.agentId);
            });
        });

        document.querySelectorAll('.stop-agent-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                await this.stopAgent(e.target.dataset.agentId);
            });
        });

        document.querySelectorAll('.delete-agent-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                if (confirm('Delete this agent?')) {
                    await this.deleteAgent(e.target.dataset.agentId);
                }
            });
        });
    }

    async startAgent(agentId) {
        try {
            const response = await fetch(`/api/agents/${agentId}/start`, { method: 'POST' });
            if (response.ok) {
                this.showToast('Agent started successfully!', 'success');
                this.updateAgentsList();
            }
        } catch (error) {
            this.showToast('Failed to start agent', 'danger');
        }
    }

    async stopAgent(agentId) {
        try {
            const response = await fetch(`/api/agents/${agentId}/stop`, { method: 'POST' });
            if (response.ok) {
                this.showToast('Agent stopped successfully!', 'warning');
                this.updateAgentsList();
            }
        } catch (error) {
            this.showToast('Failed to stop agent', 'danger');
        }
    }

    async deleteAgent(agentId) {
        try {
            const response = await fetch(`/api/agents/${agentId}`, { method: 'DELETE' });
            if (response.ok) {
                this.showToast('Agent deleted successfully!', 'info');
                this.updateAgentsList();
            }
        } catch (error) {
            this.showToast('Failed to delete agent', 'danger');
        }
    }

    setupFormHandlers() {
        const createForm = document.querySelector('#createAgentForm');
        if (createForm) {
            createForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.createAgent(new FormData(createForm));
            });
        }
    }

    async createAgent(formData) {
        try {
            const data = {
                name: formData.get('name'),
                account_ids: formData.get('account_ids').split(',').map(id => id.trim()).filter(id => id)
            };

            const response = await fetch('/api/agents', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                this.showToast('Agent created successfully!', 'success');
                this.closeModal('createAgentModal');
                this.updateAgentsList();
                document.querySelector('#createAgentForm').reset();
            }
        } catch (error) {
            this.showToast('Failed to create agent', 'danger');
        }
    }

    setupEventListeners() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                this.updateDashboard();
                this.showToast('Dashboard refreshed!', 'info');
            }
        });
    }

    showToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    closeModal(modalId) {
        const modal = bootstrap.Modal.getInstance(document.querySelector(`#${modalId}`));
        if (modal) modal.hide();
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.fraudDashboard = new FraudDashboard();
});