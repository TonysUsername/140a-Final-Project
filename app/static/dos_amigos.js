document.addEventListener("DOMContentLoaded", () => {
    console.log("App.js Loaded");

    // Smooth scrolling for navigation links
    document.querySelectorAll("nav ul li a").forEach(link => {
        link.addEventListener("click", event => {
            event.preventDefault();
            const targetId = event.target.getAttribute("href").replace(".html", "");
            const targetSection = document.getElementById(targetId);
            if (targetSection) {
                window.scrollTo({
                    top: targetSection.offsetTop - 50,
                    behavior: "smooth"
                });
            } else {
                window.location.href = event.target.getAttribute("href");
            }
        });
    });

    // Fade-in effect for sections when scrolling
    const sections = document.querySelectorAll("section");
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = 1;
                entry.target.style.transform = "translateY(0)";
            }
        });
    }, { threshold: 0.3 });

    sections.forEach(section => {
        section.style.opacity = 0;
        section.style.transform = "translateY(20px)";
        observer.observe(section);
    });

    // Add hover effect on navigation links
    document.querySelectorAll("nav ul li a").forEach(link => {
        link.addEventListener("mouseover", () => {
            link.style.transform = "scale(1.1)";
            link.style.transition = "transform 0.2s ease-in-out";
        });
        link.addEventListener("mouseleave", () => {
            link.style.transform = "scale(1)";
        });
    });

    // Navbar hide on scroll
    let lastScrollTop = 0;
    const navbar = document.querySelector('.navbar');
    
    if (navbar) {
        window.addEventListener("scroll", () => {
            let currentScroll = window.pageYOffset || document.documentElement.scrollTop;
            if (currentScroll > lastScrollTop) {
                // Scroll down: Hide navbar
                navbar.style.top = "-80px";
            } else {
                // Scroll up: Show navbar
                navbar.style.top = "0";
            }
            lastScrollTop = currentScroll <= 0 ? 0 : currentScroll; // Prevent negative scroll values
        });
    }
});
