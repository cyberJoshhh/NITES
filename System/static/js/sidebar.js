// Sidebar functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log("Sidebar.js loaded");
    
    initializeSidebar();
    
    // Add global click handler for mobile toggle to ensure it works across interface changes
    document.addEventListener('click', function(event) {
        if (event.target.closest('#mobileMenuToggle')) {
            toggleSidebar();
        }
    }, true);
});

// Initialize sidebar and toggle functionality - make these available globally
function initializeSidebar() {
    // Get sidebar element
    const sidebar = document.getElementById('sidebar');
    
    // Get existing mobile toggle button
    const mobileToggle = document.getElementById('mobileMenuToggle');
    
    if (!sidebar || !mobileToggle) {
        console.warn("Sidebar or toggle button not found");
        return;
    }
    
    console.log("Initializing sidebar and toggle button");
    
    // Handle mobile toggle visibility
    updateMobileToggleVisibility();
    
    // Update visibility on resize
    window.addEventListener('resize', updateMobileToggleVisibility);
    
    // Add click event to mobile toggle
    if (mobileToggle) {
        mobileToggle.addEventListener('click', toggleSidebar);
        
        // Make sure the toggle button is above other elements
        mobileToggle.style.zIndex = "2000";
        mobileToggle.style.pointerEvents = "auto";
    }
    
    // Set initial sidebar state
    initializeSidebarState();
    
    // Fix main content margin
    updateMainContentMargin();
    
    // Update main content margin on resize
    window.addEventListener('resize', updateMainContentMargin);
}

// Toggle sidebar function - make it globally available
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mobileToggle = document.getElementById('mobileMenuToggle');
    
    if (!sidebar || !mobileToggle) {
        console.warn("Cannot toggle sidebar - elements not found");
        return;
    }
    
    console.log("Toggle clicked, sidebar:", sidebar);
    
    // Toggle sidebar visibility
    if (sidebar.classList.contains('active')) {
        sidebar.classList.remove('active');
        sidebar.style.left = '-280px';
        mobileToggle.innerHTML = '<i class="fas fa-bars"></i>';
        removeOverlay();
    } else {
        sidebar.classList.add('active');
        sidebar.style.left = '0px';
        mobileToggle.innerHTML = '<i class="fas fa-times"></i>';
        createOverlay();
    }
}

function updateMobileToggleVisibility() {
    const mobileToggle = document.getElementById('mobileMenuToggle');
    if (!mobileToggle) return;
    
    if (window.innerWidth <= 768) {
        mobileToggle.style.display = 'flex';
    } else {
        mobileToggle.style.display = 'none';
    }
}

// Create overlay for mobile view
function createOverlay() {
    removeOverlay(); // Remove any existing overlay
    
    const overlay = document.createElement('div');
    overlay.id = 'sidebarOverlay';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0,0,0,0.5)';
    overlay.style.zIndex = '99';
    overlay.addEventListener('click', function() {
        toggleSidebar();
    });
    
    document.body.appendChild(overlay);
}

// Remove overlay
function removeOverlay() {
    const overlay = document.getElementById('sidebarOverlay');
    if (overlay) overlay.remove();
}

// Set initial sidebar state
function initializeSidebarState() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;
    
    // Make sure sidebar has basic styles
    sidebar.style.position = 'fixed';
    sidebar.style.height = '100%';
    sidebar.style.top = '0';
    sidebar.style.zIndex = '100';
    sidebar.style.transition = 'left 0.3s ease';
    
    // Set initial position based on screen size
    if (window.innerWidth <= 768) {
        sidebar.style.left = '-280px';
        sidebar.style.width = '250px';
    } else {
        sidebar.style.left = '0';
        sidebar.style.width = '250px';
    }
    
    // Update sidebar on window resize
    window.addEventListener('resize', function() {
        if (!sidebar) return;
        
        if (window.innerWidth <= 768) {
            // Only move sidebar offscreen if it's not actively toggled
            if (!sidebar.classList.contains('active')) {
                sidebar.style.left = '-280px';
            }
        } else {
            // Always show sidebar on larger screens
            sidebar.style.left = '0';
            removeOverlay();
        }
    });
}

// Fix main content margin
function updateMainContentMargin() {
    const mainContent = document.querySelector('.main-content');
    if (!mainContent) return;
    
    if (window.innerWidth <= 768) {
        mainContent.style.marginLeft = '0';
        mainContent.style.width = '100%';
    } else {
        mainContent.style.marginLeft = '250px';
        mainContent.style.width = 'calc(100% - 250px)';
    }
}

// Function to create a debug sidebar if none exists
function createDebugSidebar() {
    console.log("Creating emergency debug sidebar");
    // Remove existing emergency sidebar if any
    const existingSidebar = document.getElementById('sidebar');
    if (existingSidebar) return existingSidebar;
    
    const debugSidebar = document.createElement('div');
    debugSidebar.id = 'sidebar';
    debugSidebar.style.position = 'fixed';
    debugSidebar.style.top = '0';
    debugSidebar.style.left = '-280px';
    debugSidebar.style.height = '100%';
    debugSidebar.style.width = '250px';
    debugSidebar.style.backgroundColor = '#fff';
    debugSidebar.style.zIndex = '1500';
    debugSidebar.style.transition = 'left 0.3s ease';
    debugSidebar.style.padding = '20px';
    debugSidebar.style.boxShadow = '0 0 10px rgba(0,0,0,0.2)';
    debugSidebar.style.overflowY = 'auto';
    
    // Add some basic content
    debugSidebar.innerHTML = `
        <h2 style="color: #52b788;">Emergency Sidebar</h2>
        <p>This is a fallback sidebar created because the original sidebar was not found.</p>
        <div style="margin-top: 20px;">
            <a href="/" style="display: block; padding: 10px; background: #f1f1f1; margin-bottom: 5px; text-decoration: none; color: #333;">Dashboard</a>
            <a href="/students" style="display: block; padding: 10px; background: #f1f1f1; margin-bottom: 5px; text-decoration: none; color: #333;">Students</a>
            <a href="/settings" style="display: block; padding: 10px; background: #f1f1f1; margin-bottom: 5px; text-decoration: none; color: #333;">Settings</a>
        </div>
    `;
    
    document.body.appendChild(debugSidebar);
    return debugSidebar;
}

// Re-initialize sidebar when document becomes visible again
document.addEventListener('visibilitychange', function() {
    if (!document.hidden) {
        initializeSidebar();
    }
});

// Ensure mobile toggle works when navigating to new pages
window.addEventListener('pageshow', function() {
    console.log("Page shown - reinitializing sidebar");
    setTimeout(initializeSidebar, 100);
});

// Add Student Modal functionality
document.addEventListener('DOMContentLoaded', function() {
    const addStudentBtn = document.querySelector('.btn-add');
    const addStudentModal = document.getElementById('addStudentModal');

    if (addStudentBtn && addStudentModal) {
        addStudentBtn.addEventListener('click', function() {
            addStudentModal.style.display = 'block';
        });
        
        // Close modal when clicking on X
        const closeBtn = addStudentModal.querySelector('.close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                addStudentModal.style.display = 'none';
            });
        }
        
        // Close modal when clicking outside
        window.addEventListener('click', function(event) {
            if (event.target === addStudentModal) {
                addStudentModal.style.display = 'none';
            }
        });
    }
    
    // Filter students functionality (if search input exists)
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            if (window.filterStudents) {
                window.filterStudents();
            }
        });
    }
}); 