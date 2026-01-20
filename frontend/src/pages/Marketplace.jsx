/**
 * Marketplace Page
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { marketplaceApi } from '../api/marketplace';
import './Marketplace.css';

const Marketplace = () => {
    const [apps, setApps] = useState([]);
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    useEffect(() => {
        loadCategories();
        loadApps();
    }, []);

    useEffect(() => {
        loadApps();
    }, [selectedCategory, searchQuery, page]);

    const loadCategories = async () => {
        try {
            const data = await marketplaceApi.getCategories();
            setCategories(data);
        } catch (err) {
            console.error('Failed to load categories:', err);
        }
    };

    const loadApps = async () => {
        try {
            setLoading(true);
            const data = await marketplaceApi.listApps(
                page,
                20,
                selectedCategory,
                searchQuery || null
            );
            setApps(data.apps);
            setTotalPages(data.pages);
        } catch (err) {
            console.error('Failed to load apps:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = (e) => {
        setSearchQuery(e.target.value);
        setPage(1);
    };

    return (
        <div className="marketplace-page">
            <div className="marketplace-header">
                <div className="marketplace-intro">
                    <h2>Discover AI Apps</h2>
                    <p>Enable powerful AI capabilities powered by MCP</p>
                </div>
                <div className="marketplace-search">
                    <span className="search-icon">🔍</span>
                    <input
                        type="text"
                        placeholder="Search apps..."
                        value={searchQuery}
                        onChange={handleSearch}
                    />
                </div>
            </div>

            <div className="marketplace-filters">
                <button
                    className={`filter-btn ${!selectedCategory ? 'active' : ''}`}
                    onClick={() => { setSelectedCategory(null); setPage(1); }}
                >
                    All
                </button>
                {categories.map((cat) => (
                    <button
                        key={cat.value}
                        className={`filter-btn ${selectedCategory === cat.value ? 'active' : ''}`}
                        onClick={() => { setSelectedCategory(cat.value); setPage(1); }}
                    >
                        {cat.label}
                    </button>
                ))}
            </div>

            {loading ? (
                <div className="marketplace-loading">
                    <div className="loader"></div>
                    <p>Loading apps...</p>
                </div>
            ) : apps.length === 0 ? (
                <div className="marketplace-empty">
                    <span className="empty-icon">📭</span>
                    <h3>No apps found</h3>
                    <p>Try a different search or category</p>
                </div>
            ) : (
                <>
                    <div className="apps-grid">
                        {apps.map((app) => (
                            <Link to={`/marketplace/${app.slug}`} key={app.id} className="app-card glass">
                                <div className="app-icon">
                                    {app.icon_url ? (
                                        <img src={app.icon_url} alt={app.name} />
                                    ) : (
                                        <span>{app.name[0]}</span>
                                    )}
                                </div>
                                <div className="app-info">
                                    <h3 className="app-name">{app.name}</h3>
                                    <p className="app-description">
                                        {app.short_description || app.description?.slice(0, 100)}
                                    </p>
                                    <div className="app-meta">
                                        <span className="app-category">{app.category?.replace('_', ' ')}</span>
                                        <span className="app-installs">{app.install_count} installs</span>
                                    </div>
                                </div>
                            </Link>
                        ))}
                    </div>

                    {totalPages > 1 && (
                        <div className="pagination">
                            <button
                                disabled={page === 1}
                                onClick={() => setPage(page - 1)}
                            >
                                ← Previous
                            </button>
                            <span>Page {page} of {totalPages}</span>
                            <button
                                disabled={page === totalPages}
                                onClick={() => setPage(page + 1)}
                            >
                                Next →
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default Marketplace;
