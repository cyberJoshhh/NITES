// Sidebar functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log("Sidebar.js loaded");
    
    // Force sidebar to consistent state on page load
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        // Reset any styles that might have been affected by other pages
        ensureSidebarConsistency();
    }
    
    // Mobile menu toggle functionality
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    
    if (mobileMenuToggle && sidebar) {
        console.log("Found mobile toggle and sidebar elements");
        
        mobileMenuToggle.addEventListener('click', function(e) {
            console.log("Mobile toggle clicked");
            e.preventDefault();
            e.stopPropagation();
            
            // Toggle sidebar visibility
            sidebar.classList.toggle('active');
            
            // Create or remove overlay
            if (sidebar.classList.contains('active')) {
                createSidebarOverlay();
            } else {
                removeSidebarOverlay();
            }
        });
    } else {
        console.error("Mobile toggle or sidebar not found");
        if (!mobileMenuToggle) console.error("Mobile toggle not found");
        if (!sidebar) console.error("Sidebar not found");
    }
    
    // Close sidebar when window is resized to larger than mobile breakpoint
    window.addEventListener('resize', function() {
        ensureSidebarConsistency();
        
        if (window.innerWidth > 576) {
            if (sidebar && sidebar.classList.contains('active')) {
                sidebar.classList.remove('active');
                removeSidebarOverlay();
            }
        }
    });
    
    // Function to ensure sidebar maintains consistent dimensions and position
    function ensureSidebarConsistency() {
        if (!sidebar) return;
        
        // Ensure core sidebar properties
        if (window.innerWidth <= 576) {
            // Mobile view
            sidebar.style.position = 'fixed';
            sidebar.style.height = '100vh';
            sidebar.style.width = '280px';
            
            if (!sidebar.classList.contains('active')) {
                sidebar.style.left = '-280px';
            }
        } else if (window.innerWidth <= 992) {
            // Tablet view
            sidebar.style.position = 'fixed';
            sidebar.style.left = '0';
            sidebar.style.top = '0';
            sidebar.style.height = '100vh';
            
            if (sidebar.classList.contains('active')) {
                sidebar.style.width = '250px';
            } else {
                sidebar.style.width = '80px';
            }
        } else {
            // Desktop view
            sidebar.style.position = 'fixed';
            sidebar.style.left = '0';
            sidebar.style.top = '0';
            sidebar.style.height = '100vh';
            sidebar.style.width = '250px';
        }
        
        // Ensure the main content is properly positioned
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            if (window.innerWidth <= 576) {
                mainContent.style.marginLeft = '0';
                mainContent.style.width = '100%';
            } else if (window.innerWidth <= 992) {
                if (sidebar.classList.contains('active')) {
                    mainContent.style.marginLeft = '250px';
                    mainContent.style.width = 'calc(100% - 250px)';
                } else {
                    mainContent.style.marginLeft = '80px';
                    mainContent.style.width = 'calc(100% - 80px)';
                }
            } else {
                mainContent.style.marginLeft = '250px';
                mainContent.style.width = 'calc(100% - 250px)';
            }
        }
    }
    
    // Function to create sidebar overlay
    function createSidebarOverlay() {
        // Remove any existing overlay first
        removeSidebarOverlay();
        
        // Create new overlay
        const overlay = document.createElement('div');
        overlay.id = 'sidebarOverlay';
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100%';
        overlay.style.height = '100%';
        overlay.style.backgroundColor = 'rgba(0,0,0,0.5)';
        overlay.style.zIndex = '99';
        
        // Close sidebar when overlay is clicked
        overlay.addEventListener('click', function() {
            if (sidebar) {
                sidebar.classList.remove('active');
                removeSidebarOverlay();
            }
        });
        
        document.body.appendChild(overlay);
        
        // Ensure sidebar is above the overlay
        if (sidebar) {
            sidebar.style.zIndex = '100';
            sidebar.style.position = 'relative';
        }
    }
    
    // Function to remove sidebar overlay
    function removeSidebarOverlay() {
        const existingOverlay = document.getElementById('sidebarOverlay');
        if (existingOverlay) {
            existingOverlay.remove();
        }
    }
    
    // Fix sidebar links to ensure they're clickable
    function fixSidebarLinks() {
        // Target all possible link elements in the sidebar
        const allSidebarElements = document.querySelectorAll('#sidebar a, #sidebar .sidebar-btn, #sidebar .logout-btn');
        
        allSidebarElements.forEach(element => {
            // Apply styles directly to ensure clickability
            element.style.pointerEvents = 'auto';
            element.style.cursor = 'pointer';
            element.style.position = 'relative';
            element.style.zIndex = '1010';
        });
    }
    
    // Call the fix function
    fixSidebarLinks();
    
    // Filter students functionality (if search input exists)
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            window.filterStudents();
        });
    }
    
    // Run consistency check whenever page changes might affect the sidebar
    document.addEventListener('visibilitychange', ensureSidebarConsistency);
});

// Add Student Modal functionality
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