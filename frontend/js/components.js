/**
 * UI Components for Dashboard
 */

// Helper function to show error messages
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toLocaleString();
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function renderSessionCard(session) {
    const statusClass = session.status || 'unknown';
    const startTime = formatDate(session.start_time);
    const endTime = session.end_time ? formatDate(session.end_time) : 'In Progress';
    
    return `
        <div class="session-card">
            <div class="session-header">
                <div>
                    <div class="session-id">${session.session_id}</div>
                    <div style="font-size: 0.875rem; color: var(--gray-600); margin-top: 0.25rem;">
                        ${startTime} - ${endTime}
                    </div>
                </div>
                <span class="session-status ${statusClass}">${statusClass}</span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 1rem; margin-top: 1rem;">
                <div>
                    <div style="font-size: 0.75rem; color: var(--gray-600);">Accounts</div>
                    <div style="font-weight: 600;">${session.total_accounts || 0}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: var(--gray-600);">Videos</div>
                    <div style="font-weight: 600;">${session.total_videos_scraped || 0}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: var(--gray-600);">Success</div>
                    <div style="font-weight: 600;">${session.successful_scrapes || 0}</div>
                </div>
                <div>
                    <div style="font-size: 0.75rem; color: var(--gray-600);">Failed</div>
                    <div style="font-weight: 600;">${session.failed_scrapes || 0}</div>
                </div>
            </div>
        </div>
    `;
}

function renderSoundCard(sound) {
    return `
        <div class="sound-card">
            <div class="sound-title">${sound.song_title || 'Unknown'}</div>
            <div class="sound-artist">${sound.artist_name || 'Unknown Artist'}</div>
            <div class="sound-stats">
                <div class="sound-stat">
                    <div class="sound-stat-value">${sound.video_count || 0}</div>
                    <div class="sound-stat-label">Videos</div>
                </div>
                <div class="sound-stat">
                    <div class="sound-stat-value">${formatNumber(sound.total_views || 0)}</div>
                    <div class="sound-stat-label">Views</div>
                </div>
                <div class="sound-stat">
                    <div class="sound-stat-value">${(sound.avg_engagement_rate || 0).toFixed(2)}%</div>
                    <div class="sound-stat-label">Engagement</div>
                </div>
            </div>
        </div>
    `;
}

function renderVideoRow(video) {
    const engagementRate = video.engagement_rate || 0;
    const engagementClass = engagementRate >= 15 ? 'high' : engagementRate >= 10 ? 'medium' : 'low';
    
    return `
        <tr>
            <td>${video.account || '-'}</td>
            <td>${video.song_title || '-'}</td>
            <td>${video.artist_name || '-'}</td>
            <td>${formatNumber(video.views || 0)}</td>
            <td>${formatNumber(video.likes || 0)}</td>
            <td><span class="engagement-badge engagement-${engagementClass}">${engagementRate.toFixed(2)}%</span></td>
            <td>${formatDate(video.upload_date)}</td>
            <td><a href="${video.url || video.tiktok_url || '#'}" target="_blank" class="video-link">View</a></td>
        </tr>
    `;
}

function showError(message) {
    return `<div style="padding: 1rem; background: #fee2e2; color: #991b1b; border-radius: 4px; margin: 1rem 0;">${message}</div>`;
}

function showLoading() {
    return '<p class="loading">Loading...</p>';
}

