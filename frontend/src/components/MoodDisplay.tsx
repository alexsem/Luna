import React from 'react';
import { useAppContext } from '../AppContext';
import { Mood } from '../types';

interface MoodDisplayProps {
    mood?: Mood;
    status?: 'online' | 'offline';
}

const MoodDisplay: React.FC = () => {
    const { mood, status } = useAppContext();

    // Map mood string to file paths in public/faces
    const moodFile = `/faces/${mood}.png`;

    return (
        <div className="mood-container">
            <h2 className="luna-title">LUNA</h2>
            <div className="luna-subtitle">Creative assistant</div>

            <div className={`mood-image-wrapper ${status}`}>
                <img
                    src={moodFile}
                    alt={`Luna is feeling ${mood}`}
                    className="mood-image"
                    key={mood}
                    onError={(e: React.SyntheticEvent<HTMLImageElement, Event>) => {
                        (e.target as HTMLImageElement).src = '/faces/neutral.png';
                    }}
                />
            </div>

            <div className="author-tag">
                Created by Alexsem
            </div>
        </div>
    );
};

export default MoodDisplay;
