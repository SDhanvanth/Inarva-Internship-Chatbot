/**
 * Enabled Apps Page
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { marketplaceApi } from '../api/marketplace';
import { formatDate } from '../utils/validation';
import './EnabledApps.css';

const EnabledApps = () => {
    const [enabledApps, setEnabledApps] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadEnabledApps();
    }, []);

    const loadEnabledApps = async () => {
        try {
            setLoading(true);
            const apps = await marketplaceApi.getEnabledApps();
            setEnabledApps(apps);
        } catch (err) {
            console.error('Failed to load enabled apps:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleDisable = async (appId) => {
        try {
            await marketplaceApi.disableApp(appId);
            setEnabledApps(prev => prev.filter(ea => ea.app.id !== appId));
        } catch (err) {
            console.error('Failed to disable app:', err);
        }
    };

    if (loading) {
        return (
            <div className="enabled-apps-loading">
                <div className="loader"></div>
            </div>
        );
    }

    return (
        <div className="enabled-apps-page">
            <div className="page-header">
                <h2>Your Enabled Apps</h2>
                <p>Apps that are active in your chat sessions</p>
            </div>

            {enabledApps.length === 0 ? (
                <div className="enabled-apps-empty glass">
                    <span className="empty-icon">⚡</span>
                    <h3>No apps enabled</h3>
                    <p>Enable apps from the marketplace to extend your chat capabilities</p>
                    <Link to="/marketplace" className="btn-primary">Browse Marketplace</Link>
                </div>
            ) : (
                <div className="enabled-apps-list">
                    {enabledApps.map((ea) => (
                        <div key={ea.id} className="enabled-app-card glass">
                            <div className="app-icon">
                                {ea.app.icon_url ? (
                                    <img src={ea.app.icon_url} alt={ea.app.name} />
                                ) : (
                                    <span>{ea.app.name[0]}</span>
                                )}
                            </div>
                            <div className="app-info">
                                <h3>{ea.app.name}</h3>
                                <p className="app-enabled-date">
                                    Enabled {formatDate(ea.enabled_at)}
                                </p>
                                {ea.granted_permissions && (
                                    <div className="granted-permissions">
                                        {ea.granted_permissions.map((perm, idx) => (
                                            <span key={idx} className="perm-badge">{perm}</span>
                                        ))}
                                    </div>
                                )}
                            </div>
                            <div className="app-actions">
                                <Link to={`/marketplace/${ea.app.slug}`} className="btn-view">
                                    View
                                </Link>
                                <button
                                    className="btn-disable"
                                    onClick={() => handleDisable(ea.app.id)}
                                >
                                    Disable
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default EnabledApps;
