/**
 * Admin Dashboard
 */
import React, { useState, useEffect } from 'react';
import { adminApi } from '../../api/admin';
import { formatDate } from '../../utils/validation';
import './AdminDashboard.css';

const AdminDashboard = () => {
    const [health, setHealth] = useState(null);
    const [serverInfo, setServerInfo] = useState(null);
    const [pendingApps, setPendingApps] = useState([]);
    const [users, setUsers] = useState([]);
    const [logs, setLogs] = useState([]);
    const [activeTab, setActiveTab] = useState('overview');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        try {
            setLoading(true);
            const [healthData, infoData, appsData, usersData, logsData] = await Promise.all([
                adminApi.getSystemHealth(),
                adminApi.getServerInfo(),
                adminApi.getPendingApps(),
                adminApi.listUsers(1, 10),
                adminApi.getRequestLogs({ limit: 20 }),
            ]);
            setHealth(healthData);
            setServerInfo(infoData);
            setPendingApps(appsData);
            setUsers(usersData);
            setLogs(logsData.logs);
        } catch (err) {
            console.error('Failed to load admin data:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleModerateApp = async (appId, status) => {
        try {
            await adminApi.moderateApp(appId, status);
            setPendingApps(prev => prev.filter(a => a.id !== appId));
        } catch (err) {
            console.error('Failed to moderate app:', err);
        }
    };

    if (loading) {
        return <div className="admin-loading"><div className="loader"></div></div>;
    }

    return (
        <div className="admin-dashboard">
            <div className="admin-tabs">
                <button className={activeTab === 'overview' ? 'active' : ''} onClick={() => setActiveTab('overview')}>Overview</button>
                <button className={activeTab === 'apps' ? 'active' : ''} onClick={() => setActiveTab('apps')}>App Moderation</button>
                <button className={activeTab === 'users' ? 'active' : ''} onClick={() => setActiveTab('users')}>Users</button>
                <button className={activeTab === 'logs' ? 'active' : ''} onClick={() => setActiveTab('logs')}>Request Logs</button>
                <button className={activeTab === 'system' ? 'active' : ''} onClick={() => setActiveTab('system')}>System Info</button>
            </div>

            {activeTab === 'overview' && (
                <div className="admin-overview">
                    <div className="stat-cards">
                        <div className="stat-card glass">
                            <span className="stat-icon">👥</span>
                            <div className="stat-info">
                                <span className="stat-value">{serverInfo?.stats?.total_users || 0}</span>
                                <span className="stat-label">Total Users</span>
                            </div>
                        </div>
                        <div className="stat-card glass">
                            <span className="stat-icon">📦</span>
                            <div className="stat-info">
                                <span className="stat-value">{serverInfo?.stats?.total_apps || 0}</span>
                                <span className="stat-label">Total Apps</span>
                            </div>
                        </div>
                        <div className="stat-card glass">
                            <span className="stat-icon">📊</span>
                            <div className="stat-info">
                                <span className="stat-value">{serverInfo?.stats?.requests_today || 0}</span>
                                <span className="stat-label">Requests Today</span>
                            </div>
                        </div>
                        <div className={`stat-card glass ${health?.status === 'healthy' ? 'healthy' : 'degraded'}`}>
                            <span className="stat-icon">{health?.status === 'healthy' ? '✅' : '⚠️'}</span>
                            <div className="stat-info">
                                <span className="stat-value">{health?.status}</span>
                                <span className="stat-label">System Status</span>
                            </div>
                        </div>
                    </div>

                    <div className="system-resources glass">
                        <h3>System Resources</h3>
                        <div className="resource-bars">
                            <div className="resource-bar">
                                <span>CPU</span>
                                <div className="bar"><div className="bar-fill" style={{ width: `${health?.system?.cpu_percent || 0}%` }}></div></div>
                                <span>{health?.system?.cpu_percent || 0}%</span>
                            </div>
                            <div className="resource-bar">
                                <span>Memory</span>
                                <div className="bar"><div className="bar-fill" style={{ width: `${health?.system?.memory_percent || 0}%` }}></div></div>
                                <span>{health?.system?.memory_percent || 0}%</span>
                            </div>
                            <div className="resource-bar">
                                <span>Disk</span>
                                <div className="bar"><div className="bar-fill" style={{ width: `${health?.system?.disk_percent || 0}%` }}></div></div>
                                <span>{health?.system?.disk_percent || 0}%</span>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {activeTab === 'apps' && (
                <div className="admin-apps">
                    <h3>Pending Apps ({pendingApps.length})</h3>
                    {pendingApps.length === 0 ? (
                        <p className="no-data">No apps pending review</p>
                    ) : (
                        <div className="pending-apps-list">
                            {pendingApps.map((app) => (
                                <div key={app.id} className="pending-app-card glass">
                                    <div className="app-info">
                                        <h4>{app.name}</h4>
                                        <p>{app.description?.slice(0, 100)}</p>
                                    </div>
                                    <div className="app-actions">
                                        <button className="btn-approve" onClick={() => handleModerateApp(app.id, 'approved')}>Approve</button>
                                        <button className="btn-reject" onClick={() => handleModerateApp(app.id, 'rejected')}>Reject</button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {activeTab === 'users' && (
                <div className="admin-users">
                    <h3>Users</h3>
                    <div className="users-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>Email</th>
                                    <th>Role</th>
                                    <th>Status</th>
                                    <th>Created</th>
                                </tr>
                            </thead>
                            <tbody>
                                {users.map((user) => (
                                    <tr key={user.id}>
                                        <td>{user.email}</td>
                                        <td><span className="role-badge">{user.role}</span></td>
                                        <td>{user.is_active ? '✅ Active' : '❌ Inactive'}</td>
                                        <td>{formatDate(user.created_at)}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {activeTab === 'logs' && (
                <div className="admin-logs">
                    <h3>Request Logs</h3>
                    <div className="logs-table">
                        <table>
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Method</th>
                                    <th>Path</th>
                                    <th>Status</th>
                                    <th>Duration</th>
                                </tr>
                            </thead>
                            <tbody>
                                {logs.map((log) => (
                                    <tr key={log.id}>
                                        <td>{formatDate(log.created_at)}</td>
                                        <td><span className={`method-${log.method.toLowerCase()}`}>{log.method}</span></td>
                                        <td className="path-cell">{log.path}</td>
                                        <td><span className={`status-${Math.floor(log.status_code / 100)}xx`}>{log.status_code}</span></td>
                                        <td>{log.response_time_ms}ms</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {activeTab === 'system' && (
                <div className="admin-system">
                    <h3>Server Information</h3>
                    <div className="system-info-grid">
                        <div className="info-card glass">
                            <h4>Application</h4>
                            <p>Version: {serverInfo?.version}</p>
                            <p>Environment: {serverInfo?.environment}</p>
                            <p>Python: {serverInfo?.python_version?.split(' ')[0]}</p>
                        </div>
                        <div className="info-card glass">
                            <h4>Services</h4>
                            <p>Database: {health?.services?.database?.status}</p>
                            <p>Redis: {health?.services?.redis?.status}</p>
                            <p>Uptime: {Math.floor((health?.uptime_seconds || 0) / 3600)}h</p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminDashboard;
