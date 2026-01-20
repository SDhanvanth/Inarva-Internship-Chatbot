/**
 * Usage Page
 */
import React, { useState, useEffect } from 'react';
import api from '../api/client';
import './Usage.css';

const Usage = () => {
    const [summary, setSummary] = useState(null);
    const [limits, setLimits] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadUsageData();
    }, []);

    const loadUsageData = async () => {
        try {
            setLoading(true);
            const [summaryRes, limitsRes] = await Promise.all([
                api.get('/usage/summary'),
                api.get('/usage/limits'),
            ]);
            setSummary(summaryRes.data);
            setLimits(limitsRes.data);
        } catch (err) {
            console.error('Failed to load usage data:', err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="usage-loading">
                <div className="loader"></div>
            </div>
        );
    }

    return (
        <div className="usage-page">
            <div className="page-header">
                <h2>Usage & Limits</h2>
                <p>Monitor your API usage and rate limits</p>
            </div>

            <div className="usage-cards">
                <div className="usage-card glass">
                    <div className="usage-icon">📊</div>
                    <div className="usage-stat">
                        <span className="stat-value">{summary?.total_requests || 0}</span>
                        <span className="stat-label">Total Requests</span>
                    </div>
                </div>
                <div className="usage-card glass">
                    <div className="usage-icon">🔤</div>
                    <div className="usage-stat">
                        <span className="stat-value">{summary?.total_tokens?.toLocaleString() || 0}</span>
                        <span className="stat-label">Tokens Used</span>
                    </div>
                </div>
                <div className="usage-card glass">
                    <div className="usage-icon">⚡</div>
                    <div className="usage-stat">
                        <span className="stat-value">{summary?.by_app?.length || 0}</span>
                        <span className="stat-label">Apps Used</span>
                    </div>
                </div>
            </div>

            {limits && (
                <div className="limits-section glass">
                    <h3>Rate Limits</h3>
                    <div className="limits-grid">
                        <div className="limit-item">
                            <span className="limit-label">Requests / Minute</span>
                            <span className="limit-value">{limits.limits.requests_per_minute}</span>
                        </div>
                        <div className="limit-item">
                            <span className="limit-label">Requests / Hour</span>
                            <span className="limit-value">{limits.limits.requests_per_hour}</span>
                        </div>
                        <div className="limit-item">
                            <span className="limit-label">Tool Calls / Minute</span>
                            <span className="limit-value">{limits.limits.tool_calls_per_minute}</span>
                        </div>
                        <div className="limit-item">
                            <span className="limit-label">Burst Size</span>
                            <span className="limit-value">{limits.limits.burst_size}</span>
                        </div>
                    </div>
                </div>
            )}

            {summary?.by_app && summary.by_app.length > 0 && (
                <div className="app-usage-section glass">
                    <h3>Usage by App</h3>
                    <div className="app-usage-list">
                        {summary.by_app.map((appUsage, idx) => (
                            <div key={idx} className="app-usage-item">
                                <span className="app-name">{appUsage.app_name || 'Default Chatbot'}</span>
                                <div className="app-usage-stats">
                                    <span>{appUsage.requests_count} requests</span>
                                    <span>{appUsage.tokens_used?.toLocaleString()} tokens</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

export default Usage;
