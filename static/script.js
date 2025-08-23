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
                showResults(data.original_url, data.results, data.total_results);
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

    function showResults(url, results, totalFound) {
        // Update source URL
        sourceUrl.textContent = url;
        
        // Update results count - count total prices found across all results
        let totalPricesFound = results.reduce((total, result) => total + (result.prices ? result.prices.length : 0), 0);
        resultsCount.textContent = `${totalFound}개 CID 검색 결과, 총 ${totalPricesFound}개 가격 발견`;
        
        // Clear previous results
        pricesList.innerHTML = '';
        
        // Add results grouped by CID
        results.forEach((result, index) => {
            const cidSection = createCIDSection(result, index + 1);
            pricesList.appendChild(cidSection);
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

    function createCIDSection(result, index) {
        const section = document.createElement('div');
        section.className = 'cid-section mb-4';
        
        // Status badge color based on result status
        let statusBadge = '';
        let statusIcon = '';
        if (result.status === 'success' && result.prices && result.prices.length > 0) {
            statusBadge = 'bg-success';
            statusIcon = 'fas fa-check-circle';
        } else if (result.status === 'no_prices') {
            statusBadge = 'bg-warning';
            statusIcon = 'fas fa-exclamation-triangle';
        } else {
            statusBadge = 'bg-danger';
            statusIcon = 'fas fa-times-circle';
        }
        
        let content = `
            <div class="card border-start border-info border-4">
                <div class="card-header">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">
                            <i class="fas fa-hashtag text-info me-2"></i>
                            CID: ${escapeHtml(result.cid)}
                        </h6>
                        <span class="badge ${statusBadge}">
                            <i class="${statusIcon} me-1"></i>
                            ${result.status === 'success' && result.prices && result.prices.length > 0 ? '가격 발견' : 
                              result.status === 'no_prices' ? '가격 없음' : '오류'}
                        </span>
                    </div>
                </div>
                <div class="card-body">
        `;
        
        if (result.prices && result.prices.length > 0) {
            result.prices.forEach((priceInfo, priceIndex) => {
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
                
                content += `
                    <div class="price-item mb-3 p-3 border rounded">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <div class="price-value h5">
                                <i class="fas fa-tag text-success me-2"></i>
                                ${escapeHtml(price)}
                            </div>
                            <span class="badge bg-secondary">#${priceIndex + 1}</span>
                        </div>
                        <div class="price-context">
                            <strong>상세정보:</strong> ${highlightedContext}
                        </div>
                    </div>
                `;
            });
        } else if (result.status === 'error') {
            content += `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>오류:</strong> ${escapeHtml(result.error || '알 수 없는 오류가 발생했습니다')}
                </div>
            `;
        } else {
            content += `
                <div class="alert alert-warning">
                    <i class="fas fa-info-circle me-2"></i>
                    이 CID에서는 평균 가격을 찾을 수 없었습니다.
                </div>
            `;
        }
        
        content += `
                </div>
            </div>
        `;
        
        section.innerHTML = content;
        return section;
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
