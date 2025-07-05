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
                this.updateAnalyses(),
                this.updateAlerts() // Add alerts update
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
            this.updateElement('#total-events-count', data.total_events);
            this.updateElement('#high-risk-count', data.high_risk_alerts);
            
            // Update active alerts count if element exists
            if (document.querySelector('#active-alerts-count')) {
                this.updateElement('#active-alerts-count', data.active_alerts);
            }
            
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
            
        } catch (error) {
            console.error('Failed to update analyses:', error);
        }
    }

    // NEW: Update alerts section
    async updateAlerts() {
        try {
            const response = await fetch('/api/alerts');
            const alerts = await response.json();
            
            const alertsContainer = document.querySelector('#alerts-list');
            if (alertsContainer) {
                alertsContainer.innerHTML = this.renderAlerts(alerts);
                this.setupAlertButtons();
            }
            
        } catch (error) {
            console.error('Failed to update alerts:', error);
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

    // NEW: Render alerts with detailed information
    renderAlerts(alerts) {
        if (!alerts || alerts.length === 0) {
            return '<div class="text-muted text-center py-3">No active alerts</div>';
        }

        return alerts.slice(0, 10).map(alert => `
            <div class="alert-item border-bottom py-2 ${alert.severity === 'CRITICAL' ? 'critical-alert' : ''}" data-alert-id="${alert.alert_id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="d-flex align-items-center gap-2 mb-1">
                            <strong>${alert.event_id}</strong>
                            <span class="badge bg-${this.getSeverityColor(alert.severity)}">${alert.severity}</span>
                            <span class="badge bg-${alert.risk_score > 0.8 ? 'danger' : 'warning'}">${alert.risk_score.toFixed(2)}</span>
                        </div>
                        <div class="text-muted small mb-1">
                            <i class="fas fa-user"></i> ${alert.account_id} | 
                            <i class="fas fa-clock"></i> ${new Date(alert.timestamp).toLocaleTimeString()}
                        </div>
                        <div class="small">
                            <strong>Indicators:</strong> ${alert.analysis_details.fraud_indicators.slice(0, 2).join(', ')}
                            ${alert.analysis_details.fraud_indicators.length > 2 ? '...' : ''}
                        </div>
                    </div>
                    <div class="d-flex flex-column gap-1">
                        <button class="btn btn-sm btn-outline-primary view-alert-btn" data-alert-id="${alert.alert_id}">
                            <i class="fas fa-eye"></i> Details
                        </button>
                        ${alert.status === 'NEW' ? 
                            `<button class="btn btn-sm btn-outline-success ack-alert-btn" data-alert-id="${alert.alert_id}">
                                <i class="fas fa-check"></i> ACK
                            </button>` : 
                            `<span class="badge bg-secondary">ACK</span>`
                        }
                    </div>
                </div>
            </div>
        `).join('');
    }

    getSeverityColor(severity) {
        switch(severity) {
            case 'CRITICAL': return 'danger';
            case 'HIGH': return 'warning';
            case 'MEDIUM': return 'info';
            default: return 'secondary';
        }
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

    // NEW: Setup alert buttons
    setupAlertButtons() {
        document.querySelectorAll('.view-alert-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const alertId = e.target.dataset.alertId;
                await this.viewAlertDetails(alertId);
            });
        });

        document.querySelectorAll('.ack-alert-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const alertId = e.target.dataset.alertId;
                await this.acknowledgeAlert(alertId);
            });
        });
    }

    // NEW: View alert details
    async viewAlertDetails(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}`);
            const alert = await response.json();
            
            this.showAlertModal(alert);
        } catch (error) {
            this.showToast('Failed to load alert details', 'danger');
        }
    }

    // NEW: Show detailed alert modal
    showAlertModal(alert) {
        const modalContent = `
            <div class="modal fade" id="alertModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header bg-${this.getSeverityColor(alert.severity)} text-white">
                            <h5 class="modal-title">
                                🚨 ${alert.severity} Risk Alert - ${alert.event_id}
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <!-- Risk Summary -->
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <h6><i class="fas fa-chart-line"></i> Risk Assessment</h6>
                                    <div class="d-flex align-items-center gap-2">
                                        <span class="badge bg-${alert.risk_score > 0.8 ? 'danger' : 'warning'} fs-6">
                                            Risk Score: ${alert.risk_score.toFixed(2)}
                                        </span>
                                        <span class="badge bg-${this.getSeverityColor(alert.severity)} fs-6">
                                            ${alert.severity}
                                        </span>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <h6><i class="fas fa-clock"></i> Event Details</h6>
                                    <p class="small mb-0">
                                        <strong>Time:</strong> ${new Date(alert.timestamp).toLocaleString()}<br>
                                        <strong>Account:</strong> ${alert.account_id}<br>
                                        <strong>Event Type:</strong> ${alert.event_details.event_type}
                                    </p>
                                </div>
                            </div>

                            <!-- Why This is Risky -->
                            <div class="mb-3">
                                <h6><i class="fas fa-exclamation-triangle"></i> Why This Event is Risky</h6>
                                <div class="bg-light p-3 rounded">
                                    ${Object.entries(alert.analysis_details.risk_breakdown).map(([key, value]) => `
                                        <div class="mb-2">
                                            <strong>${key.replace('_', ' ').toUpperCase()}:</strong> ${value}
                                        </div>
                                    `).join('')}
                                </div>
                            </div>

                            <!-- Fraud Indicators -->
                            <div class="mb-3">
                                <h6><i class="fas fa-flag"></i> Fraud Indicators Detected</h6>
                                <div class="d-flex flex-wrap gap-2">
                                    ${alert.analysis_details.fraud_indicators.map(indicator => `
                                        <span class="badge bg-danger">${indicator}</span>
                                    `).join('')}
                                </div>
                            </div>

                            <!-- AI Reasoning -->
                            <div class="mb-3">
                                <h6><i class="fas fa-brain"></i> AI Analysis Reasoning</h6>
                                <div class="bg-light p-3 rounded">
                                    <p class="mb-0">${alert.analysis_details.reasoning}</p>
                                </div>
                            </div>

                            <!-- Event Technical Details -->
                            <div class="mb-3">
                                <h6><i class="fas fa-info-circle"></i> Technical Event Details</h6>
                                <div class="row">
                                    <div class="col-md-6">
                                        <small>
                                            <strong>IP Address:</strong> ${alert.event_details.ip_address}<br>
                                            <strong>Device ID:</strong> ${alert.event_details.device_id}<br>
                                            <strong>User ID:</strong> ${alert.event_details.user_id}
                                        </small>
                                    </div>
                                    <div class="col-md-6">
                                        <small>
                                            <strong>Event Data:</strong><br>
                                            ${Object.entries(alert.event_details.event_data).map(([k,v]) => `${k}: ${v}`).join('<br>')}
                                        </small>
                                    </div>
                                </div>
                            </div>

                            <!-- Recommended Actions -->
                            <div class="mb-3">
                                <h6><i class="fas fa-tasks"></i> Recommended Actions</h6>
                                <div class="d-flex flex-wrap gap-2">
                                    ${alert.analysis_details.recommended_actions.map(action => `
                                        <span class="badge bg-info">${action.replace('_', ' ').toUpperCase()}</span>
                                    `).join('')}
                                </div>
                            </div>

                            <!-- Similar Events Context -->
                            <div class="mb-3">
                                <h6><i class="fas fa-history"></i> Historical Context</h6>
                                <p class="small text-muted">
                                    Found ${alert.analysis_details.similar_events_count} similar events in history that contributed to this risk assessment.
                                </p>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            ${alert.status === 'NEW' ? 
                                `<button type="button" class="btn btn-success" onclick="fraudDashboard.acknowledgeAlertFromModal('${alert.alert_id}')">
                                    <i class="fas fa-check"></i> Acknowledge Alert
                                </button>` : ''
                            }
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal
        const existingModal = document.querySelector('#alertModal');
        if (existingModal) existingModal.remove();
        
        // Add new modal
        document.body.insertAdjacentHTML('beforeend', modalContent);
        
        // Show modal
        const modal = new bootstrap.Modal(document.querySelector('#alertModal'));
        modal.show();
    }

    // NEW: Acknowledge alert
    async acknowledgeAlert(alertId) {
        try {
            const response = await fetch(`/api/alerts/${alertId}/acknowledge`, { method: 'POST' });
            if (response.ok) {
                this.showToast('Alert acknowledged', 'success');
                this.updateAlerts(); // Refresh alerts list
            }
        } catch (error) {
            this.showToast('Failed to acknowledge alert', 'danger');
        }
    }

    // NEW: Acknowledge from modal
    async acknowledgeAlertFromModal(alertId) {
        await this.acknowledgeAlert(alertId);
        const modal = bootstrap.Modal.getInstance(document.querySelector('#alertModal'));
        if (modal) modal.hide();
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