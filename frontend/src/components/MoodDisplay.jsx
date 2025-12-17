import React from 'react';

const MoodDisplay = ({ mood, status }) => {
    // Map mood string to file paths in public/faces
    // Default to neutral if unknown
    const moodFile = mood ? `/faces/${mood}.png` : '/faces/neutral.png';

    return (
        <div className="mood-container">
            <h2 style={{ letterSpacing: '2px', fontWeight: 300 }}>LUNA</h2>
            <img
                src={moodFile}
                alt={`Mood: ${mood}`}
                className="mood-image"
                onError={(e) => { e.target.src = '/faces/neutral.png'; }}
            />

            <div className="status-indicator">
                <div className={`dot ${status === 'online' ? 'online' : 'offline'}`}></div>
                <span>{status === 'online' ? 'SYSTEM ONLINE' : 'SYSTEM OFFLINE'}</span>
            </div>

            <div style={{ marginTop: '20px', fontSize: '0.9rem', color: '#666', textAlign: 'center' }}>
                <p>Creative Assistant</p>
                <p>v2.0 Web Interface</p>
            </div>
        </div>
    );
};

export default MoodDisplay;
