/**
 * App Details Page
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { marketplaceApi } from '../api/marketplace';
import './AppDetails.css';

const AppDetails = () => {
    const { appSlug } = useParams();
    const navigate = useNavigate();
    const [app, setApp] = useState(null);
    const [loading, setLoading] = useState(true);
    const [enabling, setEnabling] = useState(false);
    const [isEnabled, setIsEnabled] = useState(false);

    useEffect(() => {
        loadApp();
        checkIfEnabled();
    }, [appSlug]);

    const loadApp = async () => {
        try {
            setLoading(true);
            const data = await marketplaceApi.getApp(appSlug);
            setApp(data);
        } catch (err) {
            console.error('Failed to load app:', err);
        } finally {
            setLoading(false);
        }
    };

    const checkIfEnabled = async () => {
        try {
            const enabledApps = await marketplaceApi.getEnabledApps();
            const found = enabledApps.find(ea => ea.app.slug === appSlug);
            setIsEnabled(!!found);
        } catch (err) {
            console.error('Failed to check enabled status:', err);
        }
    };

    const handleEnable = async () => {
        try {
            setEnabling(true);
            await marketplaceApi.enableApp(app.id);
            setIsEnabled(true);
        } catch (err) {
            console.error('Failed to enable app:', err);
        } finally {
            setEnabling(false);
        }
    };

    const handleDisable = async () => {
        try {
            setEnabling(true);
            await marketplaceApi.disableApp(app.id);
            setIsEnabled(false);
        } catch (err) {
            console.error('Failed to disable app:', err);
        } finally {
            setEnabling(false);
        }
    };

    if (loading) {
        return (
            <div className="app-details-loading">
                <div className="loader"></div>
            </div>
        );
    }

    if (!app) {
        return (
            <div className="app-details-error">
                <h2>App not found</h2>
                <button onClick={() => navigate('/marketplace')}>Back to Marketplace</button>
            </div>
        );
    }

    return (
        <div className="app-details-page">
            <button className="back-btn" onClick={() => navigate('/marketplace')}>
                ← Back to Marketplace
            </button>

            <div className="app-details-header glass">
                <div className="app-icon-large">
                    {app.icon_url ? (
                        <img src={app.icon_url} alt={app.name} />
                    ) : (
                        <span>{app.name[0]}</span>
                    )}
                </div>
                <div className="app-header-info">
                    <h1>{app.name}</h1>
                    <p className="app-category-badge">{app.category?.replace('_', ' ')}</p>
                    <p className="app-stats">{app.install_count} installs • v{app.version}</p>
                </div>
                <div className="app-header-actions">
                    {isEnabled ? (
                        <button
                            className="btn-disable"
                            onClick={handleDisable}
                            disabled={enabling}
                        >
                            {enabling ? 'Disabling...' : 'Disable App'}
                        </button>
                    ) : (
                        <button
                            className="btn-enable"
                            onClick={handleEnable}
                            disabled={enabling}
                        >
                            {enabling ? 'Enabling...' : 'Enable App'}
                        </button>
                    )}
                </div>
            </div>

            <div className="app-details-content">
                <div className="app-description-section">
                    <h2>About</h2>
                    <p>{app.description || 'No description available.'}</p>
                </div>

                {app.permissions && app.permissions.scopes && (
                    <div className="app-permissions-section">
                        <h2>Permissions</h2>
                        <ul className="permissions-list">
                            {app.permissions.scopes.map((perm, idx) => (
                                <li key={idx}>
                                    <span className="perm-icon">🔐</span>
                                    {perm}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                <div className="app-links-section">
                    {app.documentation_url && (
                        <a href={app.documentation_url} target="_blank" rel="noopener noreferrer">
                            📖 Documentation
                        </a>
                    )}
                    {app.support_email && (
                        <a href={`mailto:${app.support_email}`}>
                            📧 Support
                        </a>
                    )}
                    {app.privacy_policy_url && (
                        <a href={app.privacy_policy_url} target="_blank" rel="noopener noreferrer">
                            🔒 Privacy Policy
                        </a>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AppDetails;
