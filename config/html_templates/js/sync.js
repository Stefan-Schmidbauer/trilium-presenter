// Window Synchronization for Main Presentation

class PresentationSync {
    constructor() {
        this.currentSlide = 1;
        this.totalSlides = 0;
        this.init();
    }
    
    init() {
        // Initialize sync channel
        if (typeof BroadcastChannel !== 'undefined') {
            this.syncChannel = new BroadcastChannel('slidev-sync');
            console.log('Main: BroadcastChannel initialized');
            this.syncChannel.addEventListener('message', (event) => {
                console.log('Main: Received sync message:', event.data);
                if (event.data.type === 'navigate') {
                    console.log('Main: Current slide:', this.currentSlide, 'Target slide:', event.data.slide);
                    if (event.data.slide !== this.currentSlide) {
                        console.log('Main: Navigating to slide', event.data.slide, '(from presenter)');
                        this.navigateToSlide(event.data.slide, true); // Skip sync back to presenter
                    } else {
                        console.log('Main: Already on target slide, skipping navigation');
                    }
                }
            });
        } else {
            console.error('Main: BroadcastChannel not supported in this browser');
        }
        
        // Detect current slide from URL
        this.detectCurrentSlide();
        
        // Override navigation to sync
        this.interceptNavigation();
        
        // Add presenter mode button only if enabled in config
        if (window.navConfig && window.navConfig.showPresenterLink) {
            this.addPresenterButton();
        }
    }
    
    detectCurrentSlide() {
        const path = window.location.pathname;
        const filename = path.split('/').pop();
        
        if (filename === 'index.html' || filename === '') {
            this.currentSlide = 1;
        } else {
            const match = filename.match(/slide(\d+)\.html/);
            if (match) {
                this.currentSlide = parseInt(match[1]);
            }
        }
        
        // Dynamically detect total slides by trying to fetch slide files
        this.detectTotalSlides();
    }
    
    async detectTotalSlides() {
        // Use static total slides count from generator
        this.totalSlides = {{TOTAL_SLIDES}};
        console.log('Main: Total slides set to:', this.totalSlides);
    }
    
    interceptNavigation() {
        // Override navigation button clicks
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('nav-btn')) {
                e.preventDefault();
                const href = e.target.getAttribute('href');
                this.navigateToSlideByHref(href);
            }
        });
        
        // Add keyboard navigation
        document.addEventListener('keydown', (e) => {
            switch(e.key) {
                case 'ArrowRight':
                case 'Space':
                    e.preventDefault();
                    this.nextSlide();
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    this.prevSlide();
                    break;
                case 'p':
                case 'P':
                    this.openPresenter();
                    break;
            }
        });
    }
    
    navigateToSlideByHref(href) {
        let slideNumber = 1;
        if (href === 'index.html') {
            slideNumber = 1;
        } else {
            const match = href.match(/slide(\d+)\.html/);
            if (match) {
                slideNumber = parseInt(match[1]);
            }
        }
        this.navigateToSlide(slideNumber);
    }
    
    navigateToSlide(slideNumber, skipSync = false) {
        // Bounds checking
        if (slideNumber < 1 || slideNumber > this.totalSlides) {
            console.warn('Invalid slide number:', slideNumber, 'Total slides:', this.totalSlides);
            return;
        }
        
        this.currentSlide = slideNumber;
        
        let targetFile;
        if (slideNumber === 1) {
            targetFile = 'index.html';
        } else {
            targetFile = `slide${slideNumber}.html`;
        }
        
        console.log('Navigating to slide', slideNumber, 'file:', targetFile, 'skipSync:', skipSync);
        window.location.href = targetFile;
        
        // Only sync to presenter if this navigation wasn't triggered by presenter
        if (!skipSync && this.syncChannel) {
            console.log('Main: Sending sync message to presenter');
            this.syncChannel.postMessage({
                type: 'navigate',
                slide: slideNumber
            });
        } else if (skipSync) {
            console.log('Main: Skipping sync (navigation came from presenter)');
        }
    }
    
    nextSlide() {
        if (this.currentSlide < this.totalSlides) {
            this.navigateToSlide(this.currentSlide + 1);
        }
    }
    
    prevSlide() {
        if (this.currentSlide > 1) {
            this.navigateToSlide(this.currentSlide - 1);
        }
    }
    
    addPresenterButton() {
        // Add presenter mode button to navigation
        const nav = document.querySelector('.slide-navigation');
        if (nav) {
            const presenterBtn = document.createElement('a');
            presenterBtn.href = '#';
            presenterBtn.className = 'nav-btn presenter-btn';
            presenterBtn.textContent = 'Presenter';
            presenterBtn.style.backgroundColor = '#0066cc';
            presenterBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.openPresenter();
            });
            nav.appendChild(presenterBtn);
        }
    }
    
    openPresenter() {
        // Get the current directory and construct the correct path to simple presenter
        const currentPath = window.location.pathname;
        const currentDir = currentPath.substring(0, currentPath.lastIndexOf('/'));
        const presenterPath = currentDir + '/../simple_presenter.html';
        console.log('Opening simple presenter at:', presenterPath);
        window.open(presenterPath, '_blank', 'width=1200,height=800');
    }
}

// Initialize sync when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PresentationSync();
});
