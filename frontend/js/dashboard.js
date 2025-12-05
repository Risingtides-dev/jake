/**
 * Dashboard main logic
 */

// Tab switching
document.addEventListener('DOMContentLoaded', () => {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');
            
            // Update active states
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            button.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
            
            // Load data for active tab
            loadTabData(targetTab);
        });
    });

    // Load initial dashboard data
    loadDashboardData();
    
    // Set up polling for real-time updates
    setInterval(() => {
        if (document.querySelector('.tab-content.active').id === 'dashboard') {
            loadDashboardData();
        }
    }, 5000); // Poll every 5 seconds
});

async function loadDashboardData() {
    try {
        // Load sessions
        const sessionsResponse = await api.getSessions(5);
        const sessions = sessionsResponse.sessions || [];
        
        // Render recent sessions
        const recentSessionsContainer = document.getElementById('recent-sessions');
        if (sessions.length > 0) {
            recentSessionsContainer.innerHTML = sessions.map(renderSessionCard).join('');
        } else {
            recentSessionsContainer.innerHTML = '<p>No sessions found</p>';
        }
        
        // Load stats from most recent session
        if (sessions.length > 0) {
            const latestSession = sessions[0];
            await loadSessionStats(latestSession.session_id);
        }
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        document.getElementById('recent-sessions').innerHTML = showError('Failed to load dashboard data');
    }
}

async function loadSessionStats(sessionId) {
    try {
        const [videosResponse, soundsResponse] = await Promise.all([
            api.getVideos({ session_id: sessionId }),
            api.getSounds(sessionId)
        ]);
        
        const videos = videosResponse.videos || [];
        const sounds = soundsResponse.sounds || [];
        
        // Calculate totals
        const totalViews = videos.reduce((sum, v) => sum + (v.views || 0), 0);
        const totalLikes = videos.reduce((sum, v) => sum + (v.likes || 0), 0);
        
        // Update stats
        document.getElementById('stat-total-videos').textContent = formatNumber(videos.length);
        document.getElementById('stat-total-sounds').textContent = sounds.length;
        document.getElementById('stat-total-accounts').textContent = new Set(videos.map(v => v.account)).size;
        document.getElementById('stat-total-views').textContent = formatNumber(totalViews);
    } catch (error) {
        console.error('Error loading session stats:', error);
    }
}

async function loadTabData(tab) {
    switch(tab) {
        case 'sessions':
            await loadSessions();
            break;
        case 'videos':
            await loadVideos();
            break;
        case 'sounds':
            await loadSounds();
            break;
        case 'reports':
            // Reports tab doesn't need pre-loading
            break;
    }
}

async function loadSessions() {
    const container = document.getElementById('sessions-list');
    container.innerHTML = showLoading();
    
    try {
        const response = await api.getSessions(50);
        const sessions = response.sessions || [];
        
        if (sessions.length > 0) {
            container.innerHTML = sessions.map(renderSessionCard).join('');
        } else {
            container.innerHTML = '<p>No sessions found</p>';
        }
    } catch (error) {
        console.error('Error loading sessions:', error);
        container.innerHTML = showError('Failed to load sessions');
    }
}

async function loadVideos() {
    const tbody = document.getElementById('videos-tbody');
    tbody.innerHTML = '<tr><td colspan="8" class="loading">Loading videos...</td></tr>';
    
    try {
        const response = await api.getVideos();
        const videos = response.videos || [];
        
        if (videos.length > 0) {
            tbody.innerHTML = videos.map(renderVideoRow).join('');
            
            // Populate filters
            const accounts = [...new Set(videos.map(v => v.account).filter(Boolean))];
            const sounds = [...new Set(videos.map(v => v.sound_key).filter(Boolean))];
            
            const accountFilter = document.getElementById('video-account-filter');
            accountFilter.innerHTML = '<option value="">All Accounts</option>' +
                accounts.map(acc => `<option value="${acc}">${acc}</option>`).join('');
            
            const soundFilter = document.getElementById('video-sound-filter');
            soundFilter.innerHTML = '<option value="">All Sounds</option>' +
                sounds.map(sound => `<option value="${sound}">${sound}</option>`).join('');
            
            // Set up filter handlers
            setupVideoFilters(videos);
        } else {
            tbody.innerHTML = '<tr><td colspan="8">No videos found</td></tr>';
        }
    } catch (error) {
        console.error('Error loading videos:', error);
        tbody.innerHTML = '<tr><td colspan="8">Failed to load videos</td></tr>';
    }
}

function setupVideoFilters(allVideos) {
    const searchInput = document.getElementById('video-search');
    const accountFilter = document.getElementById('video-account-filter');
    const soundFilter = document.getElementById('video-sound-filter');
    const tbody = document.getElementById('videos-tbody');
    
    function filterVideos() {
        const searchTerm = searchInput.value.toLowerCase();
        const selectedAccount = accountFilter.value;
        const selectedSound = soundFilter.value;
        
        const filtered = allVideos.filter(video => {
            const matchesSearch = !searchTerm || 
                (video.song_title && video.song_title.toLowerCase().includes(searchTerm)) ||
                (video.artist_name && video.artist_name.toLowerCase().includes(searchTerm)) ||
                (video.account && video.account.toLowerCase().includes(searchTerm));
            
            const matchesAccount = !selectedAccount || video.account === selectedAccount;
            const matchesSound = !selectedSound || video.sound_key === selectedSound;
            
            return matchesSearch && matchesAccount && matchesSound;
        });
        
        if (filtered.length > 0) {
            tbody.innerHTML = filtered.map(renderVideoRow).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="8">No videos match filters</td></tr>';
        }
    }
    
    searchInput.addEventListener('input', filterVideos);
    accountFilter.addEventListener('change', filterVideos);
    soundFilter.addEventListener('change', filterVideos);
}

async function loadSounds() {
    const container = document.getElementById('sounds-list');
    container.innerHTML = showLoading();
    
    try {
        const response = await api.getSounds();
        const sounds = response.sounds || [];
        
        if (sounds.length > 0) {
            container.innerHTML = sounds.map(renderSoundCard).join('');
        } else {
            container.innerHTML = '<p>No sounds found</p>';
        }
    } catch (error) {
        console.error('Error loading sounds:', error);
        container.innerHTML = showError('Failed to load sounds');
    }
}

// Report generation
document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generate-report-btn');
    const downloadBtn = document.getElementById('download-report-btn');
    const statusDiv = document.getElementById('report-status');
    
    if (generateBtn) {
        generateBtn.addEventListener('click', async () => {
            generateBtn.disabled = true;
            statusDiv.innerHTML = 'Generating report...';
            
            try {
                const response = await api.generateReport();
                statusDiv.innerHTML = '<div style="color: green;">Report generated successfully!</div>';
                downloadBtn.disabled = false;
                downloadBtn.onclick = () => {
                    // TODO: Implement report download
                    alert('Report download not yet implemented');
                };
            } catch (error) {
                console.error('Error generating report:', error);
                statusDiv.innerHTML = showError('Failed to generate report: ' + error.message);
            } finally {
                generateBtn.disabled = false;
            }
        });
    }
});

