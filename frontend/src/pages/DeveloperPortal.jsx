/**
 * Developer Portal Page
 */
import React, { useState, useEffect } from 'react';
import { developerApi } from '../api/marketplace';
import { formatDate } from '../utils/validation';
import './DeveloperPortal.css';

const DeveloperPortal = () => {
    const [apps, setApps] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        mcp_endpoint: '',
        category: 'other',
    });
    const [creating, setCreating] = useState(false);

    useEffect(() => {
        loadApps();
    }, []);

    const loadApps = async () => {
        try {
            setLoading(true);
            const data = await developerApi.listMyApps();
            setApps(data.apps);
        } catch (err) {
            console.error('Failed to load apps:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async (e) => {
        e.preventDefault();
        console.log("handleCreate called with:", formData);
        try {
            setCreating(true);
            const response = await developerApi.createApp(formData);
            console.log("App created:", response);
            alert("App created successfully!");
            setShowCreateModal(false);
            setFormData({ name: '', description: '', mcp_endpoint: '', category: 'other' });
            loadApps();
        } catch (err) {
            console.error('Failed to create app:', err);
            alert(`Failed to create app: ${err.message || 'Unknown error'}`);
        } finally {
            setCreating(false);
        }
    };

    const handleSubmitForReview = async (appId) => {
        try {
            await developerApi.submitForReview(appId);
            loadApps();
        } catch (err) {
            console.error('Failed to submit for review:', err);
        }
    };

    const handleDelete = async (appId) => {
        if (window.confirm('Are you sure you want to delete this app?')) {
            try {
                await developerApi.deleteApp(appId);
                loadApps();
            } catch (err) {
                console.error('Failed to delete app:', err);
            }
        }
    };

    const getStatusBadge = (status) => {
        const colors = {
            pending: 'warning',
            approved: 'success',
            rejected: 'error',
            suspended: 'error',
        };
        return <span className={`status-badge status-${colors[status]}`}>{status}</span>;
    };

    return (
        <div className="developer-page">
            <div className="page-header">
                <div>
                    <h2>Developer Portal</h2>
                    <p>Create and manage your MCP AI applications</p>
                </div>
                <button className="btn-create" onClick={() => setShowCreateModal(true)}>
                    + Create New App
                </button>
            </div>

            {loading ? (
                <div className="developer-loading"><div className="loader"></div></div>
            ) : apps.length === 0 ? (
                <div className="developer-empty glass">
                    <span className="empty-icon">🛠️</span>
                    <h3>No apps yet</h3>
                    <p>Create your first MCP-powered AI application</p>
                    <button className="btn-create" onClick={() => setShowCreateModal(true)}>
                        + Create New App
                    </button>
                </div>
            ) : (
                <div className="developer-apps-list">
                    {apps.map((app) => (
                        <div key={app.id} className="developer-app-card glass">
                            <div className="app-icon">
                                <span>{app.name[0]}</span>
                            </div>
                            <div className="app-info">
                                <h3>{app.name}</h3>
                                <p className="app-meta">
                                    {getStatusBadge(app.status)} • v{app.version} • {app.install_count} installs
                                </p>
                                <p className="app-created">Created {formatDate(app.created_at)}</p>
                            </div>
                            <div className="app-actions">
                                {app.status === 'rejected' && (
                                    <button className="btn-submit" onClick={() => handleSubmitForReview(app.id)}>
                                        Resubmit
                                    </button>
                                )}
                                {app.status !== 'pending' && app.status !== 'approved' && (
                                    <button className="btn-submit" onClick={() => handleSubmitForReview(app.id)}>
                                        Submit for Review
                                    </button>
                                )}
                                <button className="btn-delete" onClick={() => handleDelete(app.id)}>
                                    Delete
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Create App Modal */}
            {showCreateModal && (
                <div className="modal-overlay">
                    <div className="modal-content glass">
                        <h3>Create New App</h3>
                        <form onSubmit={handleCreate}>
                            <div className="form-group">
                                <label>App Name</label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Description</label>
                                <textarea
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    rows={3}
                                />
                            </div>
                            <div className="form-group">
                                <label>MCP Endpoint URL</label>
                                <input
                                    type="text"
                                    value={formData.mcp_endpoint}
                                    onChange={(e) => setFormData({ ...formData, mcp_endpoint: e.target.value })}
                                    placeholder="https://your-mcp-server.com"
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label>Category</label>
                                <select
                                    value={formData.category}
                                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                                >
                                    <option value="productivity">Productivity</option>
                                    <option value="development">Development</option>
                                    <option value="communication">Communication</option>
                                    <option value="data_analysis">Data Analysis</option>
                                    <option value="content">Content</option>
                                    <option value="automation">Automation</option>
                                    <option value="integration">Integration</option>
                                    <option value="other">Other</option>
                                </select>
                            </div>
                            <div className="modal-actions">
                                <button type="button" className="btn-cancel" onClick={() => setShowCreateModal(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn-create" disabled={creating}>
                                    {creating ? 'Creating...' : 'Create App'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DeveloperPortal;
