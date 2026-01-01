import React from 'react';

const MoodDisplay = ({ mood, status }) => {
    // Map mood string to file paths in public/faces
    // Default to neutral if unknown
    const moodFile = mood ? `/faces/${mood}.png` : '/faces/neutral.png';

    return (
        <div className="mood-container" style={{ textAlign: 'center' }}>
            <h2 style={{ letterSpacing: '2px', fontWeight: 300, marginBottom: '0' }}>LUNA</h2>
            <div style={{ fontSize: '0.8rem', color: '#888', marginBottom: '20px' }}>Creative assistant</div>

            <img
                src={moodFile}
                alt={`Mood: ${mood}`}
                className="mood-image"
                onError={(e) => { e.target.src = '/faces/neutral.png'; }}
            />

            <div style={{ marginTop: '10px', fontSize: '0.7rem', color: '#555' }}>
                Created by Alexsem
            </div>
        </div>
    );
};

export default MoodDisplay;
