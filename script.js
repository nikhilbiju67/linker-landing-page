// Linkker Website - Interactions & Animations

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initScrollAnimations();
    initInteractions();
});

// ==================== NAVIGATION ====================
function initNavigation() {
    const navbar = document.querySelector('.navbar');
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.querySelector('.nav-menu');

    // Navbar scroll effect
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            requestAnimationFrame(() => {
                if (window.scrollY > 50) {
                    navbar.style.background = getComputedStyle(document.documentElement)
                        .getPropertyValue('--surface').trim() === '#0A0A0F'
                        ? 'rgba(10, 10, 15, 0.95)' : 'rgba(250, 250, 250, 0.95)';
                    navbar.style.boxShadow = '0 1px 20px rgba(0,0,0,0.08)';
                } else {
                    navbar.style.background = '';
                    navbar.style.boxShadow = '';
                }
                ticking = false;
            });
            ticking = true;
        }
    });

    // Smooth scroll for nav links
    document.querySelectorAll('.nav-link, .nav-cta').forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            if (href && href.startsWith('#')) {
                e.preventDefault();
                const target = document.getElementById(href.slice(1));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
        });
    });

    // Mobile toggle
    if (navToggle) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
        });
    }
}

// ==================== SCROLL ANIMATIONS ====================
function initScrollAnimations() {
    // AOS-style intersection observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Respect data-aos-delay
                const delay = parseInt(entry.target.dataset.aosDelay) || 0;
                setTimeout(() => {
                    entry.target.classList.add('aos-animate');
                }, delay);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -40px 0px'
    });

    document.querySelectorAll('[data-aos]').forEach(el => observer.observe(el));

    // Counter animation for hero stats
    initCounterAnimation();
}

function initCounterAnimation() {
    const statNumbers = document.querySelectorAll('.hero-stat-number');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateValue(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    statNumbers.forEach(el => observer.observe(el));
}

function animateValue(element) {
    const text = element.textContent.trim();
    const match = text.match(/^([\d.]+)(.*)$/);
    if (!match) return;

    const target = parseFloat(match[1]);
    const suffix = match[2];
    const isFloat = text.includes('.');
    const duration = 1500;
    const start = performance.now();

    function update(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = target * eased;

        element.textContent = (isFloat ? current.toFixed(1) : Math.round(current)) + suffix;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

// ==================== INTERACTIONS ====================
function initInteractions() {
    // Ripple effect on buttons
    document.querySelectorAll('.btn, .download-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const rect = btn.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height) * 2;
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            const ripple = document.createElement('span');
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.25);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple-effect 0.6s ease-out forwards;
                pointer-events: none;
            `;
            btn.style.position = 'relative';
            btn.style.overflow = 'hidden';
            btn.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    });

    // Magnetic effect on feature icons
    document.querySelectorAll('.feature-card').forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;
            const icon = card.querySelector('.feature-icon');
            if (icon) {
                icon.style.transform = `translate(${x * 8}px, ${y * 8}px) scale(1.05)`;
            }
        });

        card.addEventListener('mouseleave', () => {
            const icon = card.querySelector('.feature-icon');
            if (icon) {
                icon.style.transform = '';
            }
        });
    });

    // Tilt effect on hero card
    const heroCard = document.querySelector('.hero-card');
    if (heroCard) {
        const wrapper = heroCard.parentElement;
        wrapper.addEventListener('mousemove', (e) => {
            const rect = wrapper.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width - 0.5;
            const y = (e.clientY - rect.top) / rect.height - 0.5;
            heroCard.style.transform = `perspective(800px) rotateY(${x * 8}deg) rotateX(${-y * 8}deg) translateY(0)`;
        });

        wrapper.addEventListener('mouseleave', () => {
            heroCard.style.transform = '';
        });
    }
}

// Inject keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple-effect {
        to { transform: scale(1); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Reduced motion check
if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.body.classList.add('reduced-motion');
}
