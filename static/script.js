// 전역 변수
let currentUrl = '';
let currentStep = 0;
let allResults = [];
let searchResults = [];
let cardResults = [];
let lowestPrice = null;
let lowestPriceUrl = '';
let lowestPriceCidName = '';
const totalSteps = 17; // 검색창리스트(9) + 카드리스트(8)

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

// 이벤트 리스너 설정
document.addEventListener('DOMContentLoaded', function() {
    scrapeForm.addEventListener('submit', handleFormSubmit);
    continueBtn.addEventListener('click', continueAnalysis);
    newSearchBtn.addEventListener('click', startNewSearch);
    
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

// 폼 제출 처리
function handleFormSubmit(e) {
    e.preventDefault();
    
    const url = urlInput.value.trim();
    if (!url) {
        showError('URL을 입력해주세요.');
        return;
    }
    
    // 초기화
    currentUrl = url;
    currentStep = 0;
    allResults = [];
    searchResults = [];
    cardResults = [];
    lowestPrice = null;
    lowestPriceUrl = '';
    lowestPriceCidName = '';
    
    // UI 초기화
    hideAllSections();
    showProgressSection();
    
    // 첫 번째 CID 분석 시작
    analyzeCid();
}

// CID 분석 실행
function analyzeCid() {
    if (currentStep >= totalSteps) {
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
        hideLoading();
        
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
        hideLoading();
        showError('분석 중 오류가 발생했습니다: ' + error.message);
    });
}

// 결과 처리
function processResult(data) {
    allResults.push(data);
    
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
    
    // 최저가 섹션 표시
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
        lowestPriceEl.textContent = formatPrice(lowestPrice);
        lowestCidNameEl.textContent = lowestPriceCidName;
        openLowestPriceBtnEl.disabled = false;
    }
}

// 카드 결과 표시
function displayCardResult(data) {
    const container = document.getElementById('cardResultsContainer');
    
    const cardCol = document.createElement('div');
    cardCol.className = 'col-md-6 col-lg-4 mb-3';
    
    const hasPrice = data.prices && data.prices.length > 0;
    const price = hasPrice ? data.prices[0].price : '가격 없음';
    const cardClass = hasPrice ? 'border-success' : 'border-warning';
    const badgeClass = hasPrice ? 'bg-success' : 'bg-warning';
    const badgeText = hasPrice ? '가격 발견' : '가격 없음';
    
    cardCol.innerHTML = `
        <div class="card ${cardClass}">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">${data.cid_name}</h6>
                <span class="badge ${badgeClass}">${badgeText}</span>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <h5 class="text-primary">${price}</h5>
                </div>
                <button class="btn btn-outline-primary btn-sm w-100 card-open-btn" 
                        data-url="${data.url}" 
                        ${!hasPrice ? 'disabled' : ''}>
                    <i class="fas fa-external-link-alt"></i>
                    창열기
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

// 진행률 업데이트
function updateProgress() {
    const progressText = document.getElementById('progressText');
    const progressBar = document.getElementById('progressBar');
    const currentCidNameEl = document.getElementById('currentCidName');
    const currentPhaseEl = document.getElementById('currentPhase');
    const loadingCid = document.getElementById('loadingCid');
    
    const step = currentStep + 1;
    const percentage = Math.round((step / totalSteps) * 100);
    
    // 진행률 %로 표시
    if (progressText) {
        progressText.textContent = `${percentage}%`;
    }
    progressBar.style.width = `${percentage}%`;
    
    // 현재 단계 정보 업데이트
    if (currentStep < allCids.length) {
        const currentCid = allCids[currentStep];
        if (currentCidNameEl) {
            currentCidNameEl.textContent = currentCid.name;
        }
        
        // 현재 페이즈 표시
        const isSearchPhase = currentStep < searchCids.length;
        if (currentPhaseEl) {
            currentPhaseEl.textContent = isSearchPhase ? '검색창리스트' : '카드리스트';
        }
        currentPhaseEl.className = `badge ${isSearchPhase ? 'bg-primary' : 'bg-info'}`;
        
        if (loadingCid) {
            if (loadingCid) {
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
    const totalResults = allResults.reduce((sum, result) => sum + result.found_count, 0);
    const totalResultsEl = document.getElementById('totalResults');
    if (totalResultsEl) {
        totalResultsEl.textContent = totalResults;
    }
    
    completeSection.style.display = 'block';
    hideContinueButton();
    hideProgressSection();
    
    completeSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// 새 검색 시작
function startNewSearch() {
    currentUrl = '';
    currentStep = 0;
    allResults = [];
    searchResults = [];
    cardResults = [];
    lowestPrice = null;
    lowestPriceUrl = '';
    lowestPriceCidName = '';
    
    hideAllSections();
    urlInput.value = '';
    urlInput.focus();
    
    // 결과 컨테이너 초기화
    document.getElementById('cardResultsContainer').innerHTML = '';
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
    return numericPrice.toLocaleString();
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
    loadingIndicator.style.display = 'none';
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
    hideLowestPriceSection();
    hideCardResultsSection();
    hideContinueButton();
    completeSection.style.display = 'none';
}

// 잘못된 링크 모달 표시 및 입력창 초기화
function showInvalidLinkModal(message) {
    // Bootstrap Alert로 모달처럼 표시
    const alertHtml = `
        <div class="alert alert-warning alert-dismissible fade show position-fixed" 
             style="top: 20px; left: 50%; transform: translateX(-50%); z-index: 9999; max-width: 500px; width: 90%;" 
             role="alert">
            <h6 class="alert-heading">
                <i class="fas fa-exclamation-triangle"></i> 링크 오류
            </h6>
            <p class="mb-2">${message.replace('\n', '<br>')}</p>
            <hr>
            <p class="mb-0">
                <button type="button" class="btn btn-primary btn-sm me-2 modal-ok-btn">
                    <i class="fas fa-check"></i> OK
                </button>
                <a href="/guide" target="_blank" class="btn btn-outline-primary btn-sm">
                    <i class="fas fa-question-circle"></i> 사용법 보기
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