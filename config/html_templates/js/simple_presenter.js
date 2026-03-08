// Simple Presenter JavaScript
class SimplePresenter {
    constructor() {
        this.totalSlides = 0; // Will be detected dynamically
        this.currentSlide = 1;
        this.notes = {};
        this.slideTitles = {};
        this.syncChannel = null;
        
        this.initializeSync();
        this.loadNotes();
        this.initializePresenter();
        this.setupKeyboardNavigation();
    }
    
    async initializePresenter() {
        await this.detectTotalSlides();
        await this.loadSlideTitles();
        this.createSlideList();
        this.updateDisplay();
    }
    
    async detectTotalSlides() {
        // Use static total slides count from generator
        this.totalSlides = {{TOTAL_SLIDES}};
        console.log('Presenter: Total slides set to:', this.totalSlides);
    }
    
    initializeSync() {
        try {
            this.syncChannel = new BroadcastChannel('slidev-sync');
            this.syncChannel.onmessage = (event) => {
                if (event.data.type === 'navigate') {
                    this.receiveSlideChange(event.data.slide);
                }
            };
        } catch (error) {
            console.warn('BroadcastChannel not supported, sync disabled');
        }
    }
    
    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            switch(e.key) {
                case 'ArrowRight':
                case 'ArrowDown':
                case 'Space':
                    e.preventDefault();
                    this.nextSlide();
                    break;
                case 'ArrowLeft':
                case 'ArrowUp':
                    e.preventDefault();
                    this.previousSlide();
                    break;
                case 'Home':
                    e.preventDefault();
                    this.goToSlide(1);
                    break;
                case 'End':
                    e.preventDefault();
                    this.goToSlide(this.totalSlides);
                    break;
            }
        });
    }
    
    nextSlide() {
        if (this.currentSlide < this.totalSlides) {
            this.goToSlide(this.currentSlide + 1);
        }
    }
    
    previousSlide() {
        if (this.currentSlide > 1) {
            this.goToSlide(this.currentSlide - 1);
        }
    }
    
    async loadNotes() {
        try {
            const response = await fetch('notes.json');
            if (response.ok) {
                this.notes = await response.json();
            }
        } catch (error) {
            console.warn('Error loading notes:', error);
        }
    }
    
    async loadSlideTitles() {
        for (let i = 1; i <= this.totalSlides; i++) {
            try {
                const slideFile = i === 1 ? 'slides/index.html' : `slides/slide${i}.html`;
                const response = await fetch(slideFile);
                if (response.ok) {
                    const html = await response.text();
                    const title = this.extractTitleFromHTML(html);
                    this.slideTitles[i] = title || `Slide ${i}`;
                } else {
                    this.slideTitles[i] = `Slide ${i}`;
                }
            } catch (error) {
                this.slideTitles[i] = `Slide ${i}`;
            }
        }
    }
    
    extractTitleFromHTML(html) {
        const h1Match = html.match(/<h1[^>]*>([^<]+)<\/h1>/i);
        if (h1Match) {
            return h1Match[1].trim();
        }
        return null;
    }
    
    convertMarkdownToHTML(markdown) {
        if (!markdown || markdown.trim() === '') {
            return 'No notes for this slide.';
        }
        
        let html = markdown;
        
        // Convert markdown links
        html = html.replace(/\[([^\]]+)\]\(([^\)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
        
        // Convert URLs
        html = html.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
        
        // Convert bold
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        
        // Convert italic
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
        
        // Convert inline code
        html = html.replace(/`(.+?)`/g, '<code>$1</code>');
        
        // Convert lines to paragraphs and lists
        const lines = html.split('\n');
        const processedLines = [];
        let inList = false;
        
        for (let line of lines) {
            line = line.trim();
            if (line.startsWith('- ') || line.startsWith('* ')) {
                if (!inList) {
                    processedLines.push('<ul>');
                    inList = true;
                }
                processedLines.push('<li>' + line.substring(2) + '</li>');
            } else {
                if (inList) {
                    processedLines.push('</ul>');
                    inList = false;
                }
                if (line.length > 0) {
                    processedLines.push('<p>' + line + '</p>');
                }
            }
        }
        
        if (inList) {
            processedLines.push('</ul>');
        }
        
        return processedLines.join('');
    }
    
    createSlideList() {
        const slideList = document.getElementById('slide-list');
        slideList.innerHTML = '';
        
        for (let i = 1; i <= this.totalSlides; i++) {
            const slideItem = document.createElement('div');
            slideItem.className = 'slide-item';
            slideItem.dataset.slide = i;
            
            const slideNumber = document.createElement('span');
            slideNumber.className = 'slide-number';
            slideNumber.textContent = i + '.';
            
            const slideTitle = document.createElement('span');
            slideTitle.className = 'slide-title';
            slideTitle.textContent = this.slideTitles[i] || `Slide ${i}`;
            
            slideItem.appendChild(slideNumber);
            slideItem.appendChild(slideTitle);
            
            slideItem.addEventListener('click', () => {
                this.goToSlide(i);
            });
            
            slideList.appendChild(slideItem);
        }
    }
    
    updateSlideList() {
        const slideItems = document.querySelectorAll('.slide-item');
        slideItems.forEach(item => {
            const slideNum = parseInt(item.dataset.slide);
            const titleSpan = item.querySelector('.slide-title');
            if (titleSpan) {
                titleSpan.textContent = this.slideTitles[slideNum] || `Slide ${slideNum}`;
            }
        });
    }
    
    goToSlide(slideNumber) {
        this.currentSlide = slideNumber;
        this.updateDisplay();
        this.syncToMain();
    }
    
    receiveSlideChange(slideNumber) {
        this.currentSlide = slideNumber;
        this.updateDisplay();
    }
    
    updateDisplay() {
        const currentSlide = document.getElementById('current-slide');
        currentSlide.textContent = this.slideTitles[this.currentSlide] || ('Slide ' + this.currentSlide);
        
        const nextSlide = document.getElementById('next-slide');
        if (this.currentSlide < this.totalSlides) {
            const nextSlideNum = this.currentSlide + 1;
            nextSlide.textContent = 'Next: ' + (this.slideTitles[nextSlideNum] || ('Slide ' + nextSlideNum));
        } else {
            nextSlide.textContent = 'End of presentation';
        }
        
        const notes = document.getElementById('notes');
        const slideNotes = this.notes[this.currentSlide.toString()] || 'No notes for this slide.';
        notes.innerHTML = this.convertMarkdownToHTML(slideNotes);
        
        // Update slide list
        const slideItems = document.querySelectorAll('.slide-item');
        slideItems.forEach(item => {
            const slideNum = parseInt(item.dataset.slide);
            item.classList.toggle('current', slideNum === this.currentSlide);
        });
        
        // Auto-scroll to keep current slide visible
        const currentSlideItem = document.querySelector('.slide-item.current');
        if (currentSlideItem) {
            currentSlideItem.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'nearest' 
            });
        }
    }
    
    syncToMain() {
        if (this.syncChannel) {
            try {
                this.syncChannel.postMessage({
                    type: 'navigate',
                    slide: this.currentSlide
                });
            } catch (error) {
                console.warn('Sync error:', error);
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new SimplePresenter();
});