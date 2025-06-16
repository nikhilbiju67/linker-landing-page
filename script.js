// Linkker Website JavaScript - Interactive Animations & Functionality

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeAnimations();
    initializeNavigation();
    initializeIntersectionObserver();
    initializeParallax();
    initializeInteractiveElements();
});

// Initialize all animations
function initializeAnimations() {
    // Animate elements on scroll
    animateOnScroll();
    
    // Initialize floating shapes animation
    initializeFloatingShapes();
    
    // Initialize hero card animations
    initializeHeroAnimations();
}

// Navigation functionality
function initializeNavigation() {
    const navbar = document.querySelector('.navbar');
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    // Scroll effect for navbar
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        // Add/remove backdrop blur based on scroll
        if (currentScroll > 50) {
            navbar.style.background = 'rgba(254, 247, 255, 0.98)';
            navbar.style.backdropFilter = 'blur(20px)';
            navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.1)';
        } else {
            navbar.style.background = 'rgba(254, 247, 255, 0.95)';
            navbar.style.backdropFilter = 'blur(16px)';
            navbar.style.boxShadow = 'none';
        }
        
        lastScroll = currentScroll;
    });
    
    // Smooth scroll for navigation links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                const offsetTop = targetElement.offsetTop - 80;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Mobile menu toggle (for future mobile implementation)
    if (navToggle) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
    }
}

// Intersection Observer for scroll animations
function initializeIntersectionObserver() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('aos-animate');
            }
        });
    }, observerOptions);
    
    // Observe all elements with data-aos attributes
    document.querySelectorAll('[data-aos]').forEach(el => {
        observer.observe(el);
    });
}

// Animate elements on scroll
function animateOnScroll() {
    const elements = document.querySelectorAll('.feature-card, .platform-card, .download-btn');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.style.transform = 'translateY(0)';
                    entry.target.style.opacity = '1';
                }, index * 100);
            }
        });
    }, { threshold: 0.1 });
    
    elements.forEach(el => {
        el.style.transform = 'translateY(30px)';
        el.style.opacity = '0';
        el.style.transition = 'all 0.6s cubic-bezier(0.4, 0.0, 0.2, 1)';
        observer.observe(el);
    });
}

// Initialize floating shapes with random movement
function initializeFloatingShapes() {
    const shapes = document.querySelectorAll('.shape');
    
    shapes.forEach((shape, index) => {
        // Add random movement
        const randomX = Math.random() * 100 - 50;
        const randomY = Math.random() * 100 - 50;
        const randomRotation = Math.random() * 360;
        const randomScale = 0.8 + Math.random() * 0.4;
        
        shape.style.transform = `translate(${randomX}px, ${randomY}px) rotate(${randomRotation}deg) scale(${randomScale})`;
        
        // Animate shapes continuously
        animateShape(shape, index);
    });
}

// Animate individual floating shape
function animateShape(shape, index) {
    const duration = 8000 + Math.random() * 4000; // 8-12 seconds
    const delay = index * 1000; // Stagger animations
    
    setInterval(() => {
        const randomX = Math.random() * 200 - 100;
        const randomY = Math.random() * 200 - 100;
        const randomRotation = Math.random() * 360;
        const randomScale = 0.8 + Math.random() * 0.4;
        
        shape.style.transition = `transform ${duration}ms cubic-bezier(0.4, 0.0, 0.2, 1)`;
        shape.style.transform = `translate(${randomX}px, ${randomY}px) rotate(${randomRotation}deg) scale(${randomScale})`;
    }, duration + delay);
}

// Initialize hero section animations
function initializeHeroAnimations() {
    const heroCard = document.querySelector('.hero-card');
    const linkItems = document.querySelectorAll('.link-item');
    
    // Animate link items with stagger effect
    linkItems.forEach((item, index) => {
        setTimeout(() => {
            item.style.animation = `slideInUp 0.6s cubic-bezier(0.4, 0.0, 0.2, 1) forwards`;
        }, index * 200);
    });
    
    // Add hover effects for link items
    linkItems.forEach(item => {
        item.addEventListener('mouseenter', () => {
            item.style.transform = 'translateY(-2px) scale(1.02)';
            item.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.15)';
        });
        
        item.addEventListener('mouseleave', () => {
            item.style.transform = 'translateY(0) scale(1)';
            item.style.boxShadow = 'none';
        });
    });
    
    // Parallax effect for hero card
    if (heroCard) {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const parallax = scrolled * 0.2;
            heroCard.style.transform = `translateY(${parallax}px)`;
        });
    }
}

// Initialize parallax effects
function initializeParallax() {
    const parallaxElements = document.querySelectorAll('.hero-visual, .floating-shapes');
    
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        
        parallaxElements.forEach((element, index) => {
            const speed = 0.3 + (index * 0.1);
            const yPos = -(scrolled * speed);
            element.style.transform = `translateY(${yPos}px)`;
        });
    });
}

// Initialize interactive elements
function initializeInteractiveElements() {
    // Button hover effects
    initializeButtonEffects();
    
    // Feature card interactions
    initializeFeatureCardEffects();
    
    // Download button animations
    initializeDownloadButtonEffects();
    
    // Logo interactions
    initializeLogoEffects();
}

// Button hover effects
function initializeButtonEffects() {
    const buttons = document.querySelectorAll('.btn');
    
    buttons.forEach(button => {
        button.addEventListener('mouseenter', () => {
            button.style.transform = 'translateY(-2px) scale(1.05)';
        });
        
        button.addEventListener('mouseleave', () => {
            button.style.transform = 'translateY(0) scale(1)';
        });
        
        // Click effect
        button.addEventListener('click', (e) => {
            const ripple = createRippleEffect(e, button);
            button.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
}

// Create ripple effect for buttons
function createRippleEffect(e, button) {
    const ripple = document.createElement('span');
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    
    ripple.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        transform: scale(0);
        animation: ripple 0.6s ease-out;
        pointer-events: none;
    `;
    
    return ripple;
}

// Feature card effects
function initializeFeatureCardEffects() {
    const featureCards = document.querySelectorAll('.feature-card');
    
    featureCards.forEach(card => {
        const icon = card.querySelector('.feature-icon');
        
        card.addEventListener('mouseenter', () => {
            if (icon) {
                icon.style.transform = 'scale(1.1) rotate(5deg)';
                icon.style.background = 'linear-gradient(135deg, var(--tertiary-color), var(--primary-color))';
            }
        });
        
        card.addEventListener('mouseleave', () => {
            if (icon) {
                icon.style.transform = 'scale(1) rotate(0deg)';
                icon.style.background = 'linear-gradient(135deg, var(--primary-color), var(--tertiary-color))';
            }
        });
    });
}

// Download button effects
function initializeDownloadButtonEffects() {
    const downloadButtons = document.querySelectorAll('.download-btn');
    
    downloadButtons.forEach(button => {
        button.addEventListener('mouseenter', () => {
            const icon = button.querySelector('.download-btn-icon');
            if (icon) {
                icon.style.transform = 'scale(1.1) rotate(5deg)';
            }
        });
        
        button.addEventListener('mouseleave', () => {
            const icon = button.querySelector('.download-btn-icon');
            if (icon) {
                icon.style.transform = 'scale(1) rotate(0deg)';
            }
        });
    });
}

// Logo interaction effects
function initializeLogoEffects() {
    const logos = document.querySelectorAll('.logo-container');
    
    logos.forEach(logo => {
        logo.addEventListener('mouseenter', () => {
            logo.style.transform = 'scale(1.1) rotate(5deg)';
            logo.style.background = 'linear-gradient(135deg, var(--tertiary-color), var(--primary-color))';
        });
        
        logo.addEventListener('mouseleave', () => {
            logo.style.transform = 'scale(1) rotate(0deg)';
            logo.style.background = 'linear-gradient(135deg, var(--primary-color), var(--tertiary-color))';
        });
    });
}

// Typing animation for hero title
function initializeTypingAnimation() {
    const titleElement = document.querySelector('.hero-title');
    if (!titleElement) return;
    
    const text = titleElement.textContent;
    titleElement.textContent = '';
    
    let i = 0;
    const typeWriter = () => {
        if (i < text.length) {
            titleElement.textContent += text.charAt(i);
            i++;
            setTimeout(typeWriter, 50);
        }
    };
    
    setTimeout(typeWriter, 1000);
}

// Smooth scroll to sections
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        const offsetTop = section.offsetTop - 80;
        window.scrollTo({
            top: offsetTop,
            behavior: 'smooth'
        });
    }
}

// Counter animation for stats
function animateCounters() {
    const counters = document.querySelectorAll('.stat-number');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = parseInt(counter.textContent.replace(/[^0-9]/g, ''));
                const suffix = counter.textContent.replace(/[0-9]/g, '');
                
                animateCounter(counter, 0, target, suffix, 2000);
                observer.unobserve(counter);
            }
        });
    });
    
    counters.forEach(counter => observer.observe(counter));
}

// Animate individual counter
function animateCounter(element, start, end, suffix, duration) {
    const range = end - start;
    const increment = end > start ? 1 : -1;
    const stepTime = Math.abs(Math.floor(duration / range));
    
    let current = start;
    const timer = setInterval(() => {
        current += increment;
        element.textContent = current + suffix;
        
        if (current === end) {
            clearInterval(timer);
        }
    }, stepTime);
}

// Initialize stats animation
setTimeout(() => {
    animateCounters();
}, 500);

// Add custom CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes ripple {
        to {
            transform: scale(2);
            opacity: 0;
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
`;

document.head.appendChild(style);

// Utility function to debounce scroll events
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

// Optimized scroll handler
const optimizedScrollHandler = debounce(() => {
    // Any expensive scroll operations go here
}, 16); // ~60fps

window.addEventListener('scroll', optimizedScrollHandler);

// Performance optimization: Reduce animations on low-end devices
function checkPerformance() {
    const isLowEndDevice = navigator.hardwareConcurrency <= 2 || 
                          navigator.deviceMemory <= 2 || 
                          /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isLowEndDevice) {
        document.body.classList.add('reduced-motion');
        
        // Disable heavy animations
        const style = document.createElement('style');
        style.textContent = `
            .reduced-motion *, 
            .reduced-motion *::before, 
            .reduced-motion *::after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        `;
        document.head.appendChild(style);
    }
}

// Check device performance on load
checkPerformance();

// Handle reduced motion preference
if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.body.classList.add('reduced-motion');
}

// Loading animation
function showLoadingAnimation() {
    const loader = document.createElement('div');
    loader.className = 'page-loader';
    loader.innerHTML = `
        <div class="loader-content">
            <div class="logo-container">
                <img src="linkker_logo.png" alt="Linkker" class="logo">
            </div>
            <div class="loader-text">Loading Linkker...</div>
        </div>
    `;
    
    const loaderStyles = `
        .page-loader {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: var(--surface);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            transition: opacity 0.5s ease-out;
        }
        
        .loader-content {
            text-align: center;
        }
        
        .loader-text {
            margin-top: 16px;
            color: var(--on-surface-variant);
            font-size: 14px;
        }
        
        .page-loader .logo-container {
            animation: pulse 1.5s infinite;
        }
    `;
    
    const styleSheet = document.createElement('style');
    styleSheet.textContent = loaderStyles;
    document.head.appendChild(styleSheet);
    
    document.body.appendChild(loader);
    
    // Hide loader after page loads
    window.addEventListener('load', () => {
        setTimeout(() => {
            loader.style.opacity = '0';
            setTimeout(() => {
                loader.remove();
                styleSheet.remove();
            }, 500);
        }, 1000);
    });
}

// Show loading animation
showLoadingAnimation();

// Initialize theme detection and adaptation
function initializeThemeAdaptation() {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
    
    function updateTheme(e) {
        if (e.matches) {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.remove('dark-theme');
        }
    }
    
    updateTheme(prefersDark);
    prefersDark.addEventListener('change', updateTheme);
}

// Initialize theme adaptation
initializeThemeAdaptation();

// Export functions for external use if needed
window.LinkkerWebsite = {
    scrollToSection,
    initializeAnimations,
    showLoadingAnimation
};