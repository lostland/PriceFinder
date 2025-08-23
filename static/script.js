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

    async function startScraping(url) {
        // Show loading state
        showLoading();
        hideError();
        hideResults();
        
        // Set button to loading state
        scrapeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 분석 중...';
        scrapeBtn.disabled = true;
        scrapeBtn.classList.add('btn-loading');

        try {
            // 스트리밍 API 요청
            const response = await fetch('/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // 스트리밍 응답 처리
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            let buffer = '';
            let allResults = [];
            let totalCids = 0;
            let completedCids = 0;
            
            // 결과 섹션 준비
            pricesList.innerHTML = '';
            resultsSection.style.display = 'block';
            
            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                
                // 각 라인 처리
                const lines = buffer.split('\n');
                buffer = lines.pop(); // 마지막 불완전한 라인은 버퍼에 보관
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const jsonData = JSON.parse(line.substring(6));
                            await handleStreamMessage(jsonData, allResults, url);
                        } catch (e) {
                            console.error('JSON parse error:', e, line);
                        }
                    }
                }
            }
            
            resetButton();
            
        } catch (error) {
            console.error('Error:', error);
            hideLoading();
            resetButton();
            showError('서버 연결에 실패했습니다. 다시 시도해주세요.');
        }
    }

    async function handleStreamMessage(message, allResults, originalUrl) {
        switch (message.type) {
            case 'start':
                updateLoadingMessage(`총 ${message.total_cids}개 CID 검색을 시작합니다...`);
                sourceUrl.textContent = originalUrl;
                break;
                
            case 'progress':
                updateLoadingMessage(
                    `단계 ${message.step}/${message.total}: CID ${message.cid} 검색 중...`,
                    message.step,
                    message.total
                );
                break;
                
            case 'result':
                allResults.push(message.data);
                addResultCardRealtime(message.data, allResults.length);
                updateResultsCount(allResults);
                break;
                
            case 'complete':
                hideLoading();
                showCompletionSummary(message, allResults);
                break;
        }
    }

    function updateLoadingMessage(text, current = null, total = null) {
        const loadingText = loadingIndicator.querySelector('h5');
        const loadingDesc = loadingIndicator.querySelector('p');
        
        if (loadingText) {
            loadingText.textContent = text;
        }
        
        // 진행률 표시
        if (current && total) {
            const percentage = Math.round((current / total) * 100);
            if (loadingDesc) {
                loadingDesc.innerHTML = `
                    <div class="progress mb-2" style="height: 8px;">
                        <div class="progress-bar progress-bar-striped progress-bar-animated bg-info" 
                             style="width: ${percentage}%"></div>
                    </div>
                    진행률: ${current}/${total} (${percentage}%)
                `;
            }
        }
    }

    function addResultCardRealtime(result, index) {
        const cidSection = createCIDSection(result, index);
        cidSection.classList.add('fade-in-up');
        pricesList.appendChild(cidSection);
        
        // 스크롤을 새 결과로 이동
        cidSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
        // 애니메이션 클래스 제거
        setTimeout(() => {
            cidSection.classList.remove('fade-in-up');
        }, 500);
    }

    function updateResultsCount(allResults) {
        const totalPricesFound = allResults.reduce((total, result) => 
            total + (result.prices ? result.prices.length : 0), 0);
        resultsCount.textContent = `${allResults.length}개 CID 검색 중, ${totalPricesFound}개 가격 발견`;
    }

    function showCompletionSummary(completeMessage, allResults) {
        // 최종 결과 카운트 업데이트
        resultsCount.textContent = `검색 완료! ${completeMessage.total_results}개 CID 검색, 총 ${completeMessage.total_prices_found}개 가격 발견`;
        
        // 완료 배너 추가
        const completionBanner = document.createElement('div');
        completionBanner.className = 'alert alert-success fade-in-up mb-4';
        completionBanner.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-check-circle fa-2x text-success me-3"></i>
                <div>
                    <h5 class="alert-heading mb-1">검색 완료!</h5>
                    <p class="mb-0">
                        모든 CID 검색을 완료했습니다. 
                        총 ${completeMessage.total_results}개 CID에서 ${completeMessage.total_prices_found}개의 가격을 발견했습니다.
                    </p>
                </div>
            </div>
        `;
        
        pricesList.insertBefore(completionBanner, pricesList.firstChild);
        
        // 완료 배너로 스크롤
        completionBanner.scrollIntoView({ behavior: 'smooth', block: 'center' });
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
