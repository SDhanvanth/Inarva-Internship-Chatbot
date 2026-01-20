/**
 * PII Detection utilities using pattern matching
 * In production, this would use TensorFlow.js with a BERT model
 */

// PII detection patterns
const PII_PATTERNS = {
    email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/gi,
    phone: /\b(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b/g,
    ssn: /\b\d{3}[-.]?\d{2}[-.]?\d{4}\b/g,
    creditCard: /\b(?:\d{4}[-. ]?){3}\d{4}\b/g,
    ipAddress: /\b(?:\d{1,3}\.){3}\d{1,3}\b/g,
};

/**
 * Detect PII in text
 */
export const detectPII = (text) => {
    const detected = [];

    for (const [type, pattern] of Object.entries(PII_PATTERNS)) {
        const matches = text.match(pattern);
        if (matches) {
            matches.forEach((match) => {
                detected.push({
                    type,
                    text: match,
                    masked: maskPII(match, type),
                });
            });
        }
    }

    return detected;
};

/**
 * Mask a PII match
 */
const maskPII = (text, type) => {
    switch (type) {
        case 'email':
            const [local, domain] = text.split('@');
            return `${local[0]}***@${domain}`;
        case 'phone':
            return text.replace(/\d(?=\d{4})/g, '*');
        case 'ssn':
            return '***-**-' + text.slice(-4);
        case 'creditCard':
            return '**** **** **** ' + text.slice(-4);
        case 'ipAddress':
            return '***.***.***.***';
        default:
            return '[REDACTED]';
    }
};

/**
 * Mask PII in text
 */
export const maskPIIInText = (text) => {
    let maskedText = text;
    const detected = detectPII(text);

    detected.forEach(({ text: piiText, type }) => {
        maskedText = maskedText.replace(
            piiText,
            `[${type.toUpperCase()}_REDACTED]`
        );
    });

    return {
        maskedText,
        detectedPII: detected,
        hasWarning: detected.length > 0,
    };
};

/**
 * Check if text contains PII
 */
export const containsPII = (text) => {
    return detectPII(text).length > 0;
};
