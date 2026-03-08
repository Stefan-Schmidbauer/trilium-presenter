// HTML Presentation Navigation System

class PresentationNavigator {
    constructor() {
        this.currentSlide = this.getCurrentSlideNumber();
        this.totalSlides = 0; // Will be detected dynamically
        this.keyboardHintTimeout = null;
        
        this.init();
    }
    
    async init() {
        await this.detectTotalSlides();
        this.setupKeyboardNavigation();
        this.setupTouchNavigation();
        this.setupProgressBar();
        
        // Show keyboard hint based on configuration
        if (window.navConfig && window.navConfig.showKeyboardHints) {
            this.showKeyboardHint();
            // Hide keyboard hint after 3 seconds
            setTimeout(() => this.hideKeyboardHint(), 3000);
        }
        
        this.updateProgressBar();
    }
    
    getCurrentSlideNumber() {
        const path = window.location.pathname;
        const filename = path.split('/').pop();
        
        if (filename === 'index.html' || filename === '') {
            return 1;
        }
        
        const match = filename.match(/slide(\d+)\.html/);
        return match ? parseInt(match[1]) : 1;
    }
    
    async detectTotalSlides() {
        // Use static total slides count from generator
        this.totalSlides = {{TOTAL_SLIDES}};
        console.log('Navigation: Total slides set to:', this.totalSlides);
    }
    
    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            switch(e.key) {
                case 'ArrowLeft':
                case 'ArrowUp':
                case 'PageUp':
                case 'Backspace':
                    e.preventDefault();
                    this.previousSlide();
                    break;
                    
                case 'ArrowRight':
                case 'ArrowDown':
                case 'PageDown':
                case ' ':
                case 'Enter':
                    e.preventDefault();
                    this.nextSlide();
                    break;
                    
                case 'Home':
                    e.preventDefault();
                    this.goToSlide(1);
                    break;
                    
                case 'End':
                    e.preventDefault();
                    this.goToSlide(this.totalSlides);
                    break;
                    
                case 'Escape':
                    this.toggleFullscreen();
                    break;
                    
                case 'h':
                case 'H':
                case '?':
                    this.showKeyboardHint();
                    break;
            }
        });
    }
    
    setupTouchNavigation() {
        let startX = 0;
        let startY = 0;
        
        document.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        });
        
        document.addEventListener('touchend', (e) => {
            if (!startX || !startY) return;
            
            // Only allow navigation if touch started in bottom 10% of screen
            const windowHeight = window.innerHeight;
            const navigationZone = windowHeight * 0.9; // Top 90% = bottom 10%
            
            if (startY < navigationZone) {
                // Touch started in content area, ignore navigation
                startX = 0;
                startY = 0;
                return;
            }
            
            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            
            const diffX = startX - endX;
            const diffY = startY - endY;
            
            // Minimum swipe distance
            const minSwipeDistance = 50;
            
            if (Math.abs(diffX) > Math.abs(diffY)) {
                // Horizontal swipe
                if (Math.abs(diffX) > minSwipeDistance) {
                    if (diffX > 0) {
                        // Swipe left - next slide
                        this.nextSlide();
                    } else {
                        // Swipe right - previous slide
                        this.previousSlide();
                    }
                }
            } else {
                // Vertical swipe
                if (Math.abs(diffY) > minSwipeDistance) {
                    if (diffY > 0) {
                        // Swipe up - next slide
                        this.nextSlide();
                    } else {
                        // Swipe down - previous slide
                        this.previousSlide();
                    }
                }
            }
            
            startX = 0;
            startY = 0;
        });
        
        // Click navigation areas
        this.setupClickNavigation();
    }
    
    setupClickNavigation() {
        // Create invisible navigation areas
        const navOverlay = document.createElement('div');
        navOverlay.className = 'nav-overlay';
        
        const prevArea = document.createElement('div');
        prevArea.className = 'nav-area prev-area';
        prevArea.addEventListener('click', () => this.previousSlide());
        
        const nextArea = document.createElement('div');
        nextArea.className = 'nav-area next-area';
        nextArea.addEventListener('click', () => this.nextSlide());
        
        navOverlay.appendChild(prevArea);
        navOverlay.appendChild(nextArea);
        document.body.appendChild(navOverlay);
    }
    
    setupProgressBar() {
        const progressBar = document.createElement('div');
        progressBar.className = 'progress-bar';
        document.body.appendChild(progressBar);
        this.progressBar = progressBar;
    }
    
    updateProgressBar() {
        if (this.progressBar) {
            const progress = (this.currentSlide / this.totalSlides) * 100;
            this.progressBar.style.width = `${progress}%`;
        }
    }
    
    showKeyboardHint() {
        let hint = document.querySelector('.keyboard-hint');
        if (!hint) {
            hint = document.createElement('div');
            hint.className = 'keyboard-hint';
            hint.innerHTML = '← → für Navigation | Esc für Vollbild | h für Hilfe';
            document.body.appendChild(hint);
        }
        
        hint.classList.remove('hidden');
        
        // Clear existing timeout
        if (this.keyboardHintTimeout) {
            clearTimeout(this.keyboardHintTimeout);
        }
        
        // Hide after 3 seconds
        this.keyboardHintTimeout = setTimeout(() => {
            this.hideKeyboardHint();
        }, 3000);
    }
    
    hideKeyboardHint() {
        const hint = document.querySelector('.keyboard-hint');
        if (hint) {
            hint.classList.add('hidden');
        }
    }
    
    previousSlide() {
        if (this.currentSlide > 1) {
            this.goToSlide(this.currentSlide - 1);
        }
    }
    
    nextSlide() {
        if (this.currentSlide < this.totalSlides) {
            this.goToSlide(this.currentSlide + 1);
        }
    }
    
    goToSlide(slideNumber) {
        if (slideNumber < 1 || slideNumber > this.totalSlides) {
            return;
        }
        
        let filename;
        if (slideNumber === 1) {
            filename = 'index.html';
        } else {
            filename = `slide${slideNumber}.html`;
        }
        
        window.location.href = filename;
    }
    
    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.log(`Error attempting to enable fullscreen: ${err.message}`);
            });
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
        }
    }
}

// Initialize navigation when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PresentationNavigator();
});

// Prevent context menu on right click (optional)
document.addEventListener('contextmenu', (e) => {
    e.preventDefault();
});

// Handle window resize
window.addEventListener('resize', () => {
    // Adjust layout if needed
    const slideContent = document.querySelector('.slide-content');
    if (slideContent) {
        // Force recalculation of layout
        slideContent.style.height = 'auto';
        setTimeout(() => {
            slideContent.style.height = '';
        }, 10);
    }
});

// Preload next slide for better performance
function preloadNextSlide() {
    const navigator = window.presentationNavigator;
    if (navigator && navigator.currentSlide < navigator.totalSlides) {
        const nextSlideNum = navigator.currentSlide + 1;
        const nextFilename = nextSlideNum === 1 ? 'index.html' : `slide${nextSlideNum}.html`;
        
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.href = nextFilename;
        document.head.appendChild(link);
    }
}

// Preload after a short delay
setTimeout(preloadNextSlide, 1000);