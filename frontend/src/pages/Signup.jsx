/**
 * Signup Page
 */
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { isValidEmail, validatePassword } from '../utils/validation';
import './Auth.css';

const Signup = () => {
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [errors, setErrors] = useState([]);
    const [loading, setLoading] = useState(false);
    const { signup } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        const newErrors = [];

        if (!isValidEmail(email)) {
            newErrors.push('Please enter a valid email address');
        }

        const passwordValidation = validatePassword(password);
        if (!passwordValidation.isValid) {
            newErrors.push(...passwordValidation.errors);
        }

        if (password !== confirmPassword) {
            newErrors.push('Passwords do not match');
        }

        if (newErrors.length > 0) {
            setErrors(newErrors);
            return;
        }

        setErrors([]);
        setLoading(true);
        const result = await signup(email, password, fullName || null);
        setLoading(false);

        if (result.success) {
            navigate('/');
        } else {
            setErrors([result.error]);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-card glass">
                <div className="auth-header">
                    <h1 className="gradient-text">Create Account</h1>
                    <p>Join Multi Chat AI today</p>
                </div>

                <form onSubmit={handleSubmit} className="auth-form">
                    {errors.length > 0 && (
                        <div className="auth-error">
                            {errors.map((error, index) => (
                                <p key={index}>{error}</p>
                            ))}
                        </div>
                    )}

                    <div className="form-group">
                        <label htmlFor="fullName">Full Name (optional)</label>
                        <input
                            id="fullName"
                            type="text"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                            placeholder="John Doe"
                            autoComplete="name"
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="your@email.com"
                            autoComplete="email"
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            autoComplete="new-password"
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="confirmPassword">Confirm Password</label>
                        <input
                            id="confirmPassword"
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            placeholder="••••••••"
                            autoComplete="new-password"
                            required
                        />
                    </div>

                    <button type="submit" className="auth-submit" disabled={loading}>
                        {loading ? 'Creating account...' : 'Create Account'}
                    </button>
                </form>

                <div className="auth-footer">
                    <p>
                        Already have an account? <Link to="/login">Sign in</Link>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Signup;
