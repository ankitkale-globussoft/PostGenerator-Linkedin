// content.js

(function() {
    console.log("LinkedIn Extractor Content Script Loaded");
    
    // Message handler
    chrome.runtime.onMessage.addListener(async (request, sender, sendResponse) => {
        if (request.action === "START_SCRAPING") {
            const { maxPosts } = request;
            startLinkedInScraping(maxPosts);
        }
    });

    async function startLinkedInScraping(maxPosts) {
        let postsFound = [];
        let postIds = new Set();
        let scrollAttempts = 0;
        const MAX_SCROLL_ATTEMPTS = 30; 

        // Extract Profile Name for filename (Prioritize Handle from URL)
        let profileName = "profile";
        
        // 1. Try to get handle from URL slug
        const urlMatch = window.location.href.match(/\/in\/([^\/\?\#]+)/);
        if (urlMatch && urlMatch[1]) {
            profileName = urlMatch[1].toLowerCase().replace(/[^a-z0-9]/gi, '_');
        } else {
            // 2. Fallback to DOM Selectors
            const nameEl = document.querySelector('h1.text-heading-xlarge') || 
                           document.querySelector('.pv-recent-activity-profile-card h3') ||
                           document.querySelector('.pv-text-details__left-panel h1') ||
                           document.querySelector('[data-test-recent-activity-header-title]');
            
            if (nameEl) {
                const fullName = nameEl.innerText.split('\n')[0].trim();
                profileName = fullName.split(' ')[0].toLowerCase().replace(/[^a-z0-9]/gi, '_');
            } else {
                // 3. Last fallback: Page Title
                profileName = document.title.split('|')[0].trim().split(' ')[0].toLowerCase().replace(/[^a-z0-9]/gi, '_');
            }
        }

        try {
            while (postsFound.length < maxPosts && scrollAttempts < MAX_SCROLL_ATTEMPTS) {
                // Expanded selectors for better coverage
                const postElements = document.querySelectorAll('.feed-shared-update-v2, .update-components-update-v2, [data-urn*="activity"]');
                
                for (const post of postElements) {
                    if (postsFound.length >= maxPosts) break;

                    const postId = post.getAttribute('data-id') || post.getAttribute('id') || post.getAttribute('data-urn');
                    if (postId && postIds.has(postId)) continue;
                    if (postId) postIds.add(postId);

                    // 1. Extract text (Handling 'see more' and nested spans)
                    let text = "";
                    
                    // Specific description wrappers
                    const textContainer = post.querySelector('.feed-shared-update-v2__description-wrapper') || 
                                          post.querySelector('.feed-shared-inline-show-more-text') ||
                                          post.querySelector('.update-components-text');
                    
                    if (textContainer) {
                        // Try to click 'see more' if it exists to get full text
                        const seeMoreBtn = textContainer.querySelector('.feed-shared-inline-show-more-text__see-more-less-toggle, .see-more');
                        if (seeMoreBtn) {
                            seeMoreBtn.click();
                            // Brief wait for expansion
                            await new Promise(r => setTimeout(r, 100));
                        }
                        text = textContainer.innerText.replace(/see more$/i, '').trim();
                    }

                    // 2. Extract engagement (Robust count extraction)
                    let engagement = 0;
                    const reactionsEl = post.querySelector('.social-details-social-counts__reactions-count .social-details-social-counts__count-value') ||
                                        post.querySelector('button[aria-label*="reactions"] .social-details-social-counts__count-value') ||
                                        post.querySelector('.social-details-social-counts__social-proof-fallback-number');
                    
                    if (reactionsEl) {
                        const countText = reactionsEl.innerText.replace(/[^0-9]/g, '');
                        if (countText) engagement = parseInt(countText);
                    } else {
                        // Fallback: check any social details item
                        const socialItem = post.querySelector('.social-details-social-counts__item');
                        if (socialItem) {
                            const countText = socialItem.innerText.replace(/[^0-9]/g, '');
                            if (countText) engagement = parseInt(countText);
                        }
                    }

                    if (text && text.length > 5) {
                        postsFound.push({ text, engagement });
                        
                        chrome.runtime.sendMessage({
                            type: "PROGRESS_UPDATE",
                            current: postsFound.length,
                            total: maxPosts,
                            status: `Extracted ${postsFound.length} posts...`
                        });
                    }
                }

                if (postsFound.length < maxPosts) {
                    window.scrollTo(0, document.body.scrollHeight);
                    scrollAttempts++;
                    await new Promise(r => setTimeout(r, 2500)); // Wait for lazy load
                }
            }

            chrome.runtime.sendMessage({
                type: "SCRAPING_COMPLETE",
                data: postsFound,
                profileName: profileName
            });

        } catch (err) {
            console.error(err);
            chrome.runtime.sendMessage({
                type: "SCRAPING_ERROR",
                error: "Error during scraping: " + err.message
            });
        }
    }
})();
