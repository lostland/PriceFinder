// Price Scraper JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('scrapeForm');
    const urlInput = document.getElementById('urlInput');
    const scrapeBtn = document.getElementById('scrapeBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const errorMessage = document.getElementById('errorMessage');
    const resultsSection = document.getElementById('resultsSection');
    const errorText = document.getElementById('errorText');
    const sourceUrl = document.getElementById('sourceUrl');
    const pricesList = document.getElementById('pricesList');
    const resultsCount = document.getElementById('resultsCount');

    // Form submission handler
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const url = urlInput.value.trim();
        if (!url) {
            showError('올바른 URL을 입력해주세요');
            return;
        }

        // Start scraping process
        startScraping(url);
    });

    // Input validation
    urlInput.addEventListener('input', function() {
        hideError();
        hideResults();
    });

    function startScraping(url) {
        // Show loading state
        showLoading();
        hideError();
        hideResults();
        
        // Set button to loading state
        scrapeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 분석 중...';
        scrapeBtn.disabled = true;
        scrapeBtn.classList.add('btn-loading');

        // Make the API request
        fetch('/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();
            resetButton();

            if (data.error) {
                showError(data.error);
                if (data.prices && data.prices.length > 0) {
                    // Show partial results even if there's an error
                    showResults(data.url || url, data.prices, data.total_found || data.prices.length);
                }
            } else if (data.success) {
                showResults(data.url, data.prices, data.total_found);
            } else {
                showError('서버에서 예상치 못한 응답이 왔습니다');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            hideLoading();
            resetButton();
            showError('서버 연결에 실패했습니다. 다시 시도해주세요.');
        });
    }

    function showLoading() {
        loadingIndicator.style.display = 'block';
        loadingIndicator.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function hideLoading() {
        loadingIndicator.style.display = 'none';
    }

    function showError(message) {
        errorText.textContent = message;
        errorMessage.style.display = 'block';
        errorMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function hideError() {
        errorMessage.style.display = 'none';
    }

    function showResults(url, prices, totalFound) {
        // Update source URL
        sourceUrl.textContent = url;
        
        // Update results count
        resultsCount.textContent = `${totalFound}개 중 ${prices.length}개 발견`;
        
        // Clear previous results
        pricesList.innerHTML = '';
        
        // Add price items
        prices.forEach((priceInfo, index) => {
            const priceItem = createPriceItem(priceInfo, index + 1);
            pricesList.appendChild(priceItem);
        });
        
        // Show results section
        resultsSection.style.display = 'block';
        resultsSection.classList.add('fade-in-up');
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Remove animation class after animation completes
        setTimeout(() => {
            resultsSection.classList.remove('fade-in-up');
        }, 500);
    }

    function hideResults() {
        resultsSection.style.display = 'none';
    }

    function createPriceItem(priceInfo, index) {
        const item = document.createElement('div');
        item.className = 'price-item';
        
        const price = priceInfo.price || 'N/A';
        const context = priceInfo.context || '컨텍스트 정보가 없습니다';
        
        // Highlight the price within the context
        let highlightedContext = context;
        if (context.includes(price)) {
            highlightedContext = context.replace(
                new RegExp(`(${escapeRegExp(price)})`, 'gi'),
                '<mark class="bg-warning text-dark">$1</mark>'
            );
        }
        
        item.innerHTML = `
            <div class="d-flex justify-content-between align-items-start mb-2">
                <div class="price-value">
                    <i class="fas fa-tag text-success me-2"></i>
                    ${escapeHtml(price)}
                </div>
                <span class="badge bg-secondary">#${index}</span>
            </div>
            <div class="price-context">
                <strong>상세정보:</strong> ${highlightedContext}
            </div>
        `;
        
        return item;
    }

    function resetButton() {
        scrapeBtn.innerHTML = '<i class="fas fa-search"></i> 방값 찾기';
        scrapeBtn.disabled = false;
        scrapeBtn.classList.remove('btn-loading');
    }

    // Utility functions
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // Auto-focus on URL input
    urlInput.focus();

    // 호텔 예약 사이트 샘플 URL
    const sampleUrls = [
        'agoda.com',
        'booking.com',
        'expedia.co.kr',
        'hotels.com'
    ];

    // Add placeholder with rotating sample URLs
    let placeholderIndex = 0;
    setInterval(() => {
        if (document.activeElement !== urlInput) {
            urlInput.placeholder = `예시: ${sampleUrls[placeholderIndex]} 또는 다른 호텔 예약 사이트 URL`;
            placeholderIndex = (placeholderIndex + 1) % sampleUrls.length;
        }
    }, 3000);
});
