// 전역 변수
let currentUrl = '';
let currentStep = 0;
let allResults = [];
let searchResults = [];
let cardResults = [];
let lowestPrice = null;
let lowestPriceUrl = '';
let lowestPriceCidName = '';
let basePrice = null; // 기준 가격 (첫 번째 결과에서 설정)
const totalSteps = 17; // 검색창리스트(9) + 카드리스트(8)
let currentLanguage = 'ko'; // 기본값: 한국어
let isAnalyzing = false; // 분석 중인 상태 추적

// 부드러운 진행률 애니메이션을 위한 변수들
let currentProgressPercentage = 0;
let targetProgressPercentage = 0;
let progressAnimationInterval = null;

// CID 정보 배열
const searchCids = [
    { name: '시크릿창', cid: '-1' },
    { name: '구글지도A', cid: '1829968' },
    { name: '구글지도B', cid: '1917614' },
    { name: '구글지도C', cid: '1833981' },
    { name: '구글 검색A', cid: '1776688' },
    { name: '구글 검색B', cid: '1922868' },
    { name: '구글 검색C', cid: '1908612' },
    { name: '네이버 검색', cid: '1729890' },
    { name: 'TripAdvisor', cid: '1587497' }
];

const cardCids = [
    { name: '카카오페이', cid: '1942636' },
    { name: '현대카드', cid: '1895693' },
    { name: '국민카드', cid: '1563295' },
    { name: '우리카드', cid: '1654104' },
    { name: 'BC카드', cid: '1748498' },
    { name: '신한카드', cid: '1760133' },
    { name: '하나카드', cid: '1729471' },
    { name: '토스', cid: '1917334' }
];

const allCids = [...searchCids, ...cardCids];

// DOM 요소들
const scrapeForm = document.getElementById('scrapeForm');
const urlInput = document.getElementById('urlInput');
const scrapeBtn = document.getElementById('scrapeBtn');
const progressSection = document.getElementById('progressSection');
const loadingIndicator = document.getElementById('loadingIndicator');
const errorMessage = document.getElementById('errorMessage');
const lowestPriceSection = document.getElementById('lowestPriceSection');
const cardResultsSection = document.getElementById('cardResultsSection');
const continueSection = document.getElementById('continueSection');
const completeSection = document.getElementById('completeSection');
const continueBtn = document.getElementById('continueBtn');
const newSearchBtn = document.getElementById('newSearchBtn');

// 번역 객체
const translations = {
    ko: {
        title: '아고다 최저 가격 자동 검색',
        subtitle1: '접속 경로 따라 달라지는 아고다 가격에 당황하셨죠?',
        subtitle2: '아고다 Magic Price 가 최저가만 깔끔하게 찾아드립니다',
        urlInput: '아고다 URL 입력',
        urlPlaceholder: '아고다 링크를 입력해 주세요',
        startAnalysis: '분석 시작',
        stopAnalysis: '분석 중단',
        guide: '사용방법',
        languageBtn: 'English',
        progress: '진행 상황',
        searchPhase: '검색창리스트',
        cardPhase: '카드리스트',
        analyzing: '분석 중...',
        loading: '가격 정보를 분석 중입니다. 잠시만 기다려주세요.',
        currentLowest: '현재 최저가',
        openLink: '창열기',
        cardComparison: '카드별 가격 비교',
        analysisComplete: '분석 완료!',
        newSearch: '새로운 검색',
        noPrice: '가격 없음',
        errorTitle: '링크 오류',
        invalidLink: '잘못된 링크를 입력한 것 같습니다\n사용법을 확인해 주세요',
        ok: 'OK'
    },
    en: {
        title: 'Agoda Lowest Price Auto Search',
        subtitle1: 'Confused by different Agoda prices depending on access route?',
        subtitle2: 'Agoda Magic Price finds the lowest prices cleanly for you',
        urlInput: 'Enter Agoda URL',
        urlPlaceholder: 'Please enter Agoda link',
        startAnalysis: 'Start Analysis',
        stopAnalysis: 'Stop Analysis',
        guide: 'Guide',
        languageBtn: '한국어',
        progress: 'Progress',
        searchPhase: 'Search Engine List',
        cardPhase: 'Card List',
        analyzing: 'Analyzing...',
        loading: 'Analyzing price information. Please wait a moment.',
        currentLowest: 'Current Lowest',
        openLink: 'Open',
        cardComparison: 'Price Comparison by Card',
        analysisComplete: 'Analysis Complete!',
        newSearch: 'New Search',
        noPrice: 'No Price',
        errorTitle: 'Link Error',
        invalidLink: 'It seems you entered an invalid link\nPlease check the usage guide',
        ok: 'OK'
    }
};

// 이벤트 리스너 설정
document.addEventListener('DOMContentLoaded', function() {
    scrapeForm.addEventListener('submit', handleFormSubmit);
    continueBtn.addEventListener('click', continueAnalysis);
    newSearchBtn.addEventListener('click', startNewSearch);
    
    // 언어 전환 버튼
    const languageToggle = document.getElementById('languageToggle');
    if (languageToggle) {
        languageToggle.addEventListener('click', toggleLanguage);
    }
    
    // 최저가 창열기 버튼
    const openLowestPriceBtn = document.getElementById('openLowestPriceBtn');
    if (openLowestPriceBtn) {
        openLowestPriceBtn.addEventListener('click', function() {
            if (lowestPriceUrl) {
                window.open(lowestPriceUrl, '_blank');
            }
        });
    }
});

// 폼 제출 처리 (분석 시작/중단 토글)
function handleFormSubmit(e) {
    e.preventDefault();
    
    if (isAnalyzing) {
        // 분석 중단
        stopAnalysis();
    } else {
        // 분석 시작
        const url = urlInput.value.trim();
        if (!url) {
            showError('URL을 입력해주세요.');
            return;
        }
        startAnalysis(url);
    }
}

// 분석 시작
function startAnalysis(url) {
    // 초기화
    currentUrl = url;
    currentStep = 0;
    allResults = [];
    searchResults = [];
    cardResults = [];
    lowestPrice = null;
    lowestPriceUrl = '';
    lowestPriceCidName = '';
    basePrice = null;
    isAnalyzing = true;
    
    // 진행률 애니메이션 초기화 및 시작
    currentProgressPercentage = 0;
    targetProgressPercentage = 0;
    startSmoothProgress();
    
    // UI 초기화 - 새로운 검색처럼 완전 초기화
    hideAllSections();
    
    // 결과 컨테이너 초기화
    document.getElementById('cardResultsContainer').innerHTML = '';
    document.getElementById('searchResultsContainer').innerHTML = '';
    
    showProgressSection();
    
    // 버튼 텍스트 변경
    updateAnalysisButton();
    
    // 첫 번째 CID 분석 시작
    analyzeCid();
}

// 분석 중단
function stopAnalysis() {
    // 분석 상태 초기화
    isAnalyzing = false;
    
    // 진행률 애니메이션 중지
    stopSmoothProgress();
    
    // 진행상황 카드 숨기기
    hideProgressCard();
    
    // 상태 초기화 (URL은 유지)
    currentStep = 0;
    allResults = [];
    searchResults = [];
    cardResults = [];
    lowestPrice = null;
    lowestPriceUrl = '';
    lowestPriceCidName = '';
    basePrice = null;
    
    // 진행률 초기화
    currentProgressPercentage = 0;
    targetProgressPercentage = 0;
    
    // UI 초기화
    hideAllSections();
    
    // 결과 컨테이너 초기화
    document.getElementById('cardResultsContainer').innerHTML = '';
    document.getElementById('searchResultsContainer').innerHTML = '';
    
    // 버튼 텍스트 변경
    updateAnalysisButton();
}

// CID 분석 실행
function analyzeCid() {
    if (currentStep >= totalSteps) {
        // 분석 완료 시 로딩 인디케이터 숨김
        loadingIndicator.style.display = 'none';
        showComplete();
        return;
    }
    
    // UI 업데이트
    updateProgress();
    showLoading();
    hideError();
    
    // API 호출
    fetch('/scrape', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            url: currentUrl,
            step: currentStep
        })
    })
    .then(response => {
        // 응답이 JSON인지 확인
        const contentType = response.headers.get('Content-Type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('서버에서 JSON이 아닌 응답을 반환했습니다 (HTML 에러 페이지 가능성)');
        }
        return response.json();
    })
    .then(data => {
        // hideLoading(); // 고정 디스플레이를 위해 주석 처리
        
        if (data.error) {
            // 첫번째 CID에서 가격을 찾지 못한 경우 - 잘못된 링크로 판단
            if (data.error_type === 'invalid_link' && data.step === 0) {
                showInvalidLinkModal(data.error);
                return;
            }
            showError(data.error);
            return;
        }
        
        // 결과 처리
        processResult(data);
        
        // 다음 단계가 있는지 확인 - 자동으로 계속 진행
        if (data.has_next) {
            // 짧은 지연 후 자동으로 다음 단계 실행
            setTimeout(() => {
                continueAnalysis();
            }, 500); // 0.5초 지연
        } else {
            showComplete();
        }
    })
    .catch(error => {
        // hideLoading(); // 고정 디스플레이를 위해 주석 처리
        showError('분석 중 오류가 발생했습니다: ' + error.message);
    });
}

// 결과 처리
function processResult(data) {
    allResults.push(data);
    
    // 첫 번째 결과에서 기준 가격 설정
    if (data.step === 1 && data.base_price) {
        basePrice = data.base_price;
    }
    
    
    // 검색창리스트 단계인지 카드리스트 단계인지 확인
    if (data.is_search_phase) {
        processSearchResult(data);
    } else {
        processCardResult(data);
    }
    
    // 검색창리스트가 완료되면 카드 결과 섹션 표시
    if (data.search_phase_completed) {
        showCardResultsSection();
    }
}

// 검색창리스트 결과 처리
function processSearchResult(data) {
    searchResults.push(data);
    
    // 검색창리스트 결과를 작은 카드로 표시
    displaySearchResult(data);
    
    // 가격이 있는 경우 최저가 업데이트
    if (data.prices && data.prices.length > 0) {
        const price = data.prices[0];  // 첫 번째 가격 사용
        const numericPrice = extractNumericPrice(price.price);
        
        if (numericPrice && (lowestPrice === null || numericPrice < lowestPrice)) {
            lowestPrice = numericPrice;
            lowestPriceUrl = data.url;
            lowestPriceCidName = data.cid_name;
            updateLowestPriceDisplay();
        }
    }
    
    // 검색창리스트 결과 섹션과 최저가 섹션 표시
    showSearchResultsSection();
    showLowestPriceSection();
}

// 카드리스트 결과 처리
function processCardResult(data) {
    cardResults.push(data);
    displayCardResult(data);
}

// 최저가 표시 업데이트
function updateLowestPriceDisplay() {
    const lowestPriceEl = document.getElementById('lowestPrice');
    const lowestCidNameEl = document.getElementById('lowestCidName');
    const openLowestPriceBtnEl = document.getElementById('openLowestPriceBtn');
    
    if (lowestPrice !== null && lowestPriceEl && lowestCidNameEl && openLowestPriceBtnEl) {
        let discountText = '';
        
        // 기준 가격과 비교하여 할인율 표시
        if (basePrice !== null) {
            const discountPercentage = (((basePrice - lowestPrice) / basePrice) * 100).toFixed(1);
            if (parseFloat(discountPercentage) > 0) {
                discountText = `${discountPercentage}% 저렴`;
            } else if (parseFloat(discountPercentage) < 0) {
                discountText = `${Math.abs(parseFloat(discountPercentage)).toFixed(1)}% 비쌈`;
            } else {
                discountText = `0.0% 저렴     `;
            }
        } else {
            discountText = '할인율 계산 중...';
        }
        
        // 할인율을 강조하는 HTML로 변경
        const discountClass = basePrice !== null && lowestPrice < basePrice ? 'discount-positive' : 
                             basePrice !== null && lowestPrice > basePrice ? 'discount-negative' : 'discount-neutral';
        
        lowestPriceEl.innerHTML = `<div class="card-result-discount-big discount-positive mb-2">${discountText}</div>`;
        lowestCidNameEl.textContent = lowestPriceCidName;
        openLowestPriceBtnEl.disabled = false;
    }
}

// 검색창리스트 결과 표시 (작은 카드)
function displaySearchResult(data) {
    const container = document.getElementById('searchResultsContainer');
    const t = translations[currentLanguage];
    
    const cardCol = document.createElement('div');
    cardCol.className = 'col-md-4 col-lg-3 mb-2';
    
    const hasPrice = data.prices && data.prices.length > 0;
    let priceDisplay = '';
    
    if (hasPrice) {
        if (data.discount_percentage !== null && data.discount_percentage !== undefined) {
            const discountText = data.discount_percentage >= 0 ? 
                `${data.discount_percentage}% 저렴` : 
                `${Math.abs(data.discount_percentage)}% 비쌈`;
            priceDisplay = `
                <div class="search-result-discount-big ${data.discount_percentage >= 0 ? 'discount-positive' : 'discount-negative'}">
                    ${discountText}
                </div>
            `;
        } else {
            priceDisplay = `<div class="search-result-discount-big discount-positive">0.0% 저렴</div>`;
        }
    } else {
        priceDisplay = `<div class="search-result-price mb-1">${t.noPrice}</div>`;
    }
    
    cardCol.innerHTML = `
        <div class="search-result-card">
            <div class="text-center">
                ${priceDisplay}
                <div class="search-result-name mb-2">${data.cid_name}</div>
                <button class="btn btn-outline-primary btn-sm search-open-btn" 
                        data-url="${data.url}" 
                        ${!hasPrice ? 'disabled' : ''}>
                    <i class="fas fa-external-link-alt"></i>
                    ${t.openLink}
                </button>
            </div>
        </div>
    `;
    
    container.appendChild(cardCol);
    
    // 창열기 버튼 이벤트 추가
    const openBtn = cardCol.querySelector('.search-open-btn');
    if (openBtn && !openBtn.disabled) {
        openBtn.addEventListener('click', function() {
            window.open(data.url, '_blank');
        });
    }
}

// 카드 결과 표시 (기존 크기)
function displayCardResult(data) {
    const container = document.getElementById('cardResultsContainer');
    const t = translations[currentLanguage];
    
    const cardCol = document.createElement('div');
    cardCol.className = 'col-md-6 col-lg-4 mb-3';
    
    const hasPrice = data.prices && data.prices.length > 0;
    const cardClass = hasPrice ? 'border-success' : 'border-warning';
    const badgeClass = hasPrice ? 'bg-success' : 'bg-warning';
    const badgeText = hasPrice ? '' : t.noPrice;
    
    let priceDisplay = '';
    if (hasPrice) {
        if (data.discount_percentage !== null && data.discount_percentage !== undefined) {
            const discountText = data.discount_percentage >= 0 ? 
                `${data.discount_percentage}% 저렴` : 
                `${Math.abs(data.discount_percentage)}% 비쌈`;
            priceDisplay = `
                <div class="card-result-discount-big ${data.discount_percentage >= 0 ? 'discount-positive' : 'discount-negative'} mb-2">
                    ${discountText}
                </div>
            `;
        } else {
            priceDisplay = `<div class="card-result-discount-big discount-positive mb-2">0.0% 저렴</div>`;
        }
    } else {
        priceDisplay = `<div class="card-result-price mb-2">${t.noPrice}</div>`;
    }
    
    cardCol.innerHTML = `
        <div class="card-result-item ${cardClass}">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h6 class="mb-0">${data.cid_name}</h6>
                ${badgeText ? `<span class="badge ${badgeClass}">${badgeText}</span>` : ''}
            </div>
            <div class="text-center">
                ${priceDisplay}
                <button class="btn btn-outline-primary btn-sm card-open-btn" 
                        data-url="${data.url}" 
                        ${!hasPrice ? 'disabled' : ''}>
                    <i class="fas fa-external-link-alt"></i>
                    ${t.openLink}
                </button>
            </div>
        </div>
    `;
    
    container.appendChild(cardCol);
    
    // 창열기 버튼 이벤트 추가
    const openBtn = cardCol.querySelector('.card-open-btn');
    if (openBtn && !openBtn.disabled) {
        openBtn.addEventListener('click', function() {
            window.open(data.url, '_blank');
        });
    }
}

// 디버그 결과 표시 (개발용)
function displayDebugResult(data) {
    const container = document.getElementById('debugResultsContainer');
    
    const resultCard = document.createElement('div');
    resultCard.className = 'card mb-3';
    
    const statusBadge = data.found_count > 0 ? 
        `<span class="badge bg-success">${data.found_count}개 발견</span>` :
        `<span class="badge bg-warning">가격 없음</span>`;
    
    let pricesHtml = '';
    if (data.prices && data.prices.length > 0) {
        pricesHtml = data.prices.map(price => `
            <div class="price-item mb-3">
                <div class="d-flex justify-content-between align-items-center">
                    <span class="price-value h6 mb-0 text-success">${price.price}</span>
                    <small class="text-muted">${data.process_time}초</small>
                </div>
                <div class="price-context mt-1">
                    <small class="text-muted">${price.context}</small>
                </div>
            </div>
        `).join('');
    } else {
        pricesHtml = '<div class="text-muted">이 CID에서는 가격을 찾지 못했습니다.</div>';
    }
    
    resultCard.innerHTML = `
        <div class="card-header d-flex justify-content-between align-items-center">
            <h6 class="mb-0">
                <i class="fas fa-tag text-info"></i>
                ${data.cid_name} (CID: ${data.cid})
            </h6>
            ${statusBadge}
        </div>
        <div class="card-body">
            <div class="mb-2">
                <small class="text-muted">
                    <i class="fas fa-link"></i>
                    URL: <span class="text-break url-display"></span>
                </small>
            </div>
            ${pricesHtml}
        </div>
    `;
    
    container.appendChild(resultCard);
    
    // URL을 안전하게 표시
    const urlSpan = resultCard.querySelector('.url-display');
    if (urlSpan) {
        urlSpan.textContent = data.url;
    }
    
    showDebugResultsSection();
}

// 계속 분석 버튼 처리
function continueAnalysis() {
    currentStep++;
    hideContinueButton();
    analyzeCid();
}

// 부드러운 진행률 애니메이션
function startSmoothProgress() {
    if (progressAnimationInterval) {
        clearInterval(progressAnimationInterval);
    }
    
    progressAnimationInterval = setInterval(() => {
        if (currentProgressPercentage < targetProgressPercentage) {
            currentProgressPercentage += 0.01;
            
            // 목표값에 도달했다면 정확히 맞춰줌
            if (currentProgressPercentage >= targetProgressPercentage) {
                currentProgressPercentage = targetProgressPercentage;
            }
            
            // 진행률 바 업데이트
            const progressText = document.getElementById('progressText');
            const progressBar = document.getElementById('progressBar');
            
            if (progressText) {
                progressText.textContent = `${Math.round(currentProgressPercentage)}%`;
            }
            if (progressBar) {
                progressBar.style.width = `${currentProgressPercentage}%`;
            }
        }
    }, 10); // 10ms마다 0.01씩 증가 (약 1초에 1% 증가)
}

// 부드러운 진행률 애니메이션 중지
function stopSmoothProgress() {
    if (progressAnimationInterval) {
        clearInterval(progressAnimationInterval);
        progressAnimationInterval = null;
    }
}

// 진행상황 카드 숨기기
function hideProgressCard() {
    const progressSection = document.getElementById('progressSection');
    if (progressSection) {
        progressSection.style.display = 'none';
    }
}

// 진행률 업데이트 (목표값만 설정)
function updateProgress() {
    const currentCidNameEl = document.getElementById('currentCidName');
    const currentPhaseEl = document.getElementById('currentPhase');
    const loadingCid = document.getElementById('loadingCid');
    
    const step = currentStep + 1;
    const percentage = Math.round((step / totalSteps) * 100);
    
    // 목표 진행률 설정 (부드러운 애니메이션으로 이동)
    targetProgressPercentage = percentage;
    
    // 현재 단계 정보 업데이트
    if (currentStep < allCids.length) {
        const currentCid = allCids[currentStep];
        if (currentCidNameEl) {
            // 첫 번째 스텝인 경우 '기준 가격'으로 표시
            if (currentStep === 0) {
                currentCidNameEl.textContent = '기준 가격';
            } else {
                currentCidNameEl.textContent = currentCid.name;
            }
        }
        
        // 현재 페이즈 표시
        const isSearchPhase = currentStep < searchCids.length;
        if (currentPhaseEl) {
            currentPhaseEl.textContent = isSearchPhase ? '검색창리스트' : '카드리스트';
        }
        currentPhaseEl.className = `badge ${isSearchPhase ? 'bg-primary' : 'bg-info'}`;
        
        if (loadingCid) {
            // 첫 번째 스텝인 경우 '기준 가격'으로 표시
            if (currentStep === 0) {
                loadingCid.textContent = '기준 가격';
            } else {
                loadingCid.textContent = currentCid.name;
            }
        }
    }
}

// 계속 버튼 표시
function showContinueButton(nextStep) {
    const nextCidInfo = document.getElementById('nextCidInfo');
    
    if (nextStep < allCids.length) {
        if (nextCidInfo) {
            nextCidInfo.textContent = allCids[nextStep].name;
        }
    }
    
    continueSection.style.display = 'block';
    continueSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// 완료 표시
function showComplete() {
    // 부드러운 진행률 애니메이션 중지
    stopSmoothProgress();
    
    // 진행률을 100%로 최종 설정
    const progressText = document.getElementById('progressText');
    const progressBar = document.getElementById('progressBar');
    if (progressText) {
        progressText.textContent = '100%';
    }
    if (progressBar) {
        progressBar.style.width = '100%';
    }
    
    const totalResults = allResults.reduce((sum, result) => sum + result.found_count, 0);
    const totalResultsEl = document.getElementById('totalResults');
    if (totalResultsEl) {
        totalResultsEl.textContent = totalResults;
    }
    
    // 분석중 창 숨기기
    loadingIndicator.style.display = 'none';
    
    completeSection.style.display = 'block';
    hideContinueButton();
    hideProgressSection();
    
    // 분석 완료 시 상태 초기화
    isAnalyzing = false;
    updateAnalysisButton();
    
    completeSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// 새 검색 시작
function startNewSearch() {
    // 부드러운 진행률 애니메이션 중지
    stopSmoothProgress();
    
    // 진행상황 카드 숨기기
    hideProgressCard();
    
    currentUrl = '';
    currentStep = 0;
    allResults = [];
    searchResults = [];
    cardResults = [];
    lowestPrice = null;
    lowestPriceUrl = '';
    lowestPriceCidName = '';
    basePrice = null;
    
    // 진행률 초기화
    currentProgressPercentage = 0;
    targetProgressPercentage = 0;
    
    hideAllSections();
    urlInput.value = '';
    urlInput.focus();
    
    // 버튼 업데이트
    isAnalyzing = false;
    updateAnalysisButton();
    
    // 결과 컨테이너 초기화
    document.getElementById('cardResultsContainer').innerHTML = '';
    document.getElementById('searchResultsContainer').innerHTML = '';
}

// 분석 버튼 텍스트 업데이트
function updateAnalysisButton() {
    const t = translations[currentLanguage];
    const startBtn = document.getElementById('scrapeBtn');
    
    if (startBtn) {
        if (isAnalyzing) {
            startBtn.innerHTML = `<i class="fas fa-stop"></i> ${t.stopAnalysis}`;
        } else {
            startBtn.innerHTML = `<i class="fas fa-search"></i> ${t.startAnalysis}`;
        }
    }
}

// 숫자 가격 추출 (비교용)
function extractNumericPrice(priceString) {
    const matches = priceString.match(/[\d,]+/);
    if (matches) {
        return parseInt(matches[0].replace(/,/g, ''));
    }
    return null;
}

// 가격 포맷팅
function formatPrice(numericPrice) {
    return '₩ ' + numericPrice.toLocaleString();
}

// UI 표시/숨기기 함수들
function showProgressSection() {
    progressSection.style.display = 'block';
}

function hideProgressSection() {
    progressSection.style.display = 'none';
}

function showLoading() {
    loadingIndicator.style.display = 'block';
}

function hideLoading() {
    // 분석 중 카드를 고정으로 두고 숨기지 않음
    // loadingIndicator.style.display = 'none';
}

function showSearchResultsSection() {
    const searchResultsSection = document.getElementById('searchResultsSection');
    if (searchResultsSection) {
        searchResultsSection.style.display = 'block';
    }
}

function hideSearchResultsSection() {
    const searchResultsSection = document.getElementById('searchResultsSection');
    if (searchResultsSection) {
        searchResultsSection.style.display = 'none';
    }
}

function showError(message) {
    const errorTextEl = document.getElementById('errorText');
    if (errorTextEl) {
        errorTextEl.textContent = message;
    }
    errorMessage.style.display = 'block';
}

function hideError() {
    errorMessage.style.display = 'none';
}

function showLowestPriceSection() {
    lowestPriceSection.style.display = 'block';
}

function hideLowestPriceSection() {
    lowestPriceSection.style.display = 'none';
}

function showCardResultsSection() {
    cardResultsSection.style.display = 'block';
}

function hideCardResultsSection() {
    cardResultsSection.style.display = 'none';
}


function hideContinueButton() {
    continueSection.style.display = 'none';
}

function hideAllSections() {
    hideProgressSection();
    hideLoading();
    hideError();
    hideSearchResultsSection();
    hideLowestPriceSection();
    hideCardResultsSection();
    hideContinueButton();
    completeSection.style.display = 'none';
}

// 잘못된 링크 모달 표시 및 입력창 초기화
function showInvalidLinkModal(message) {
    const t = translations[currentLanguage];
    
    // Bootstrap Alert로 모달처럼 표시
    const alertHtml = `
        <div class="alert alert-warning alert-dismissible fade show position-fixed" 
             style="top: 20px; left: 50%; transform: translateX(-50%); z-index: 9999; max-width: 500px; width: 90%;" 
             role="alert">
            <h6 class="alert-heading">
                <i class="fas fa-exclamation-triangle"></i> ${t.errorTitle}
            </h6>
            <p class="mb-2">${t.invalidLink.replace('\n', '<br>')}</p>
            <hr>
            <p class="mb-0">
                <button type="button" class="btn btn-primary btn-sm me-2 modal-ok-btn">
                    <i class="fas fa-check"></i> ${t.ok}
                </button>
                <a href="/guide?lang=${currentLanguage}" target="_blank" class="btn btn-outline-primary btn-sm">
                    <i class="fas fa-question-circle"></i> ${t.guide}
                </a>
            </p>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // 기존 alert 제거
    const existingAlert = document.querySelector('.alert-warning');
    if (existingAlert) {
        existingAlert.remove();
    }
    
    // 새 alert 추가
    document.body.insertAdjacentHTML('afterbegin', alertHtml);
    
    // OK 버튼 이벤트 추가
    const okBtn = document.querySelector('.modal-ok-btn');
    if (okBtn) {
        okBtn.addEventListener('click', function() {
            const alert = document.querySelector('.alert-warning');
            if (alert) {
                alert.remove();
            }
        });
    }
    
    // 입력창 초기화
    urlInput.value = '';
    urlInput.focus();
    
    // 모든 섹션 숨기기
    hideAllSections();
    
    // 5초 후 자동 제거
    setTimeout(() => {
        const alert = document.querySelector('.alert-warning');
        if (alert) {
            alert.remove();
        }
    }, 8000);
}

// 언어 전환
function toggleLanguage() {
    currentLanguage = currentLanguage === 'ko' ? 'en' : 'ko';
    updateLanguage();
}

// 언어 업데이트
function updateLanguage() {
    const t = translations[currentLanguage];
    
    // 페이지 제목과 설명
    const titleEl = document.querySelector('.dynamic-title');
    if (titleEl) titleEl.textContent = t.title;
    
    const subtitlePs = document.querySelectorAll('.subtitle-description p');
    if (subtitlePs[0]) subtitlePs[0].textContent = t.subtitle1;
    if (subtitlePs[1]) subtitlePs[1].textContent = t.subtitle2;
    
    // URL 입력 관련
    const urlInputTitle = document.querySelector('.card-title');
    if (urlInputTitle) urlInputTitle.innerHTML = `<i class="fas fa-link text-info"></i> ${t.urlInput}`;
    
    const urlInput = document.getElementById('urlInput');
    if (urlInput) urlInput.placeholder = t.urlPlaceholder;
    
    // 버튼 업데이트 (동적 텍스트)
    updateAnalysisButton();
    
    // 언어 전환 버튼
    const languageText = document.getElementById('languageText');
    if (languageText) languageText.textContent = t.languageBtn;
    
    // 사용방법 버튼
    const guideText = document.querySelector('.guide-text');
    if (guideText) guideText.textContent = t.guide;
    
    // 가이드 링크 업데이트
    const guideLink = document.getElementById('guideLink');
    if (guideLink) guideLink.href = `/guide?lang=${currentLanguage}`;
    
    // 진행률 관련
    const progressTitle = document.querySelector('#progressSection h6');
    if (progressTitle) progressTitle.textContent = t.progress;
    
    // 최저가 섹션
    const lowestTitle = document.querySelector('#lowestPriceSection h5');
    if (lowestTitle) lowestTitle.innerHTML = `<i class="fas fa-trophy"></i> ${t.currentLowest}`;
    
    const openBtn = document.getElementById('openLowestPriceBtn');
    if (openBtn) openBtn.innerHTML = `<i class="fas fa-external-link-alt"></i> ${t.openLink}`;
    
    // 카드 비교 섹션
    const cardTitle = document.querySelector('#cardResultsSection h5');
    if (cardTitle) cardTitle.innerHTML = `<i class="fas fa-credit-card"></i> ${t.cardComparison}`;
    
    // 완료 섹션
    const completeTitle = document.querySelector('#completeSection h4');
    if (completeTitle) completeTitle.textContent = t.analysisComplete;
    
    const newSearchBtn = document.getElementById('newSearchBtn');
    if (newSearchBtn) newSearchBtn.innerHTML = `<i class="fas fa-search"></i> ${t.newSearch}`;
    
    // 동적으로 생성되는 카드들 업데이트
    updateDynamicTexts();
}

// 동적 텍스트 업데이트
function updateDynamicTexts() {
    const t = translations[currentLanguage];
    
    // 진행률 페이즈 업데이트
    const currentPhase = document.getElementById('currentPhase');
    if (currentPhase) {
        const isSearchPhase = currentStep < searchCids.length;
        currentPhase.textContent = isSearchPhase ? t.searchPhase : t.cardPhase;
    }
    
    // 분석 중 텍스트 업데이트
    const analyzingTexts = document.querySelectorAll('.ms-2');
    analyzingTexts.forEach(el => {
        if (el.textContent.includes('분석 중') || el.textContent.includes('Analyzing')) {
            el.textContent = t.analyzing;
        }
    });
    
    // 로딩 텍스트 업데이트
    const loadingText = document.querySelector('#loadingIndicator p');
    if (loadingText) loadingText.textContent = t.loading;
}

// === 단계 진행 바(Loading 카드 내부) ===
function setStepProgress(percent, label) {
  const bar = document.getElementById('stepProgressBar');
  const text = document.getElementById('stepProgressText');
  const p = Math.max(0, Math.min(100, Number(percent) || 0));
  // 디버그 로그
  console.log("🔄 setStepProgress()", { percent, label, p, hasBar: !!bar, hasText: !!text });
  if (bar) bar.style.width = p + '%';
  if (text) text.textContent = (label ?? (Math.round(p) + '%'));
}
window.setStepProgress = setStepProgress;

// 실시간 서브 진행률 폴링
let stepProgressTimer = null;
function startStepProgressPolling() {
  stopStepProgressPolling();
  stepProgressTimer = setInterval(() => {
    fetch('/progress')
      .then(r => r.ok ? r.json() : null)
      .then(p => {
        if (!p) return;
        if (typeof p.pct === 'number') {
          setStepProgress(p.pct, p.msg || (p.pct + '%'));
        }
      })
      .catch(() => {});
  }, 400);
}
function stopStepProgressPolling() {
  if (stepProgressTimer) { clearInterval(stepProgressTimer); stepProgressTimer = null; }
}
