// 전역 변수
let currentUrl = '';
let currentStep = 0;
let allResults = [];
const totalSteps = 7;

// DOM 요소들
const scrapeForm = document.getElementById('scrapeForm');
const urlInput = document.getElementById('urlInput');
const scrapeBtn = document.getElementById('scrapeBtn');
const progressSection = document.getElementById('progressSection');
const loadingIndicator = document.getElementById('loadingIndicator');
const errorMessage = document.getElementById('errorMessage');
const resultsSection = document.getElementById('resultsSection');
const continueSection = document.getElementById('continueSection');
const completeSection = document.getElementById('completeSection');
const continueBtn = document.getElementById('continueBtn');
const newSearchBtn = document.getElementById('newSearchBtn');

// 이벤트 리스너 설정
document.addEventListener('DOMContentLoaded', function() {
    scrapeForm.addEventListener('submit', handleFormSubmit);
    continueBtn.addEventListener('click', continueAnalysis);
    newSearchBtn.addEventListener('click', startNewSearch);
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
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        // 결과 추가
        allResults.push(data);
        displayResult(data);
        
        // 다음 단계가 있는지 확인
        if (data.has_next) {
            showContinueButton(data.next_step);
        } else {
            showComplete();
        }
    })
    .catch(error => {
        hideLoading();
        showError('분석 중 오류가 발생했습니다: ' + error.message);
    });
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
    const currentCid = document.getElementById('currentCid');
    const loadingCid = document.getElementById('loadingCid');
    
    const step = currentStep + 1;
    const percentage = (step / totalSteps) * 100;
    
    progressText.textContent = `${step} / ${totalSteps}`;
    progressBar.style.width = `${percentage}%`;
    
    // CID 정보 업데이트
    const cidLabels = [
        '원본(1833981)', '1917614', '1829968', '1908612', 
        '1922868', '1776688', '1729890'
    ];
    
    if (currentStep < cidLabels.length) {
        currentCid.textContent = cidLabels[currentStep];
        loadingCid.textContent = cidLabels[currentStep];
    }
}

// 결과 표시
function displayResult(data) {
    const resultsContainer = document.getElementById('resultsContainer');
    
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
                    <span class="price-value h5 mb-0 text-success">${price.price}</span>
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
    
    // 다운로드 링크 생성
    const downloadLinkHtml = data.download_link ? `
        <div class="mt-3 pt-3 border-top">
            <a href="${data.download_link}" class="btn btn-sm btn-outline-primary" target="_blank">
                <i class="fas fa-download"></i>
                페이지 텍스트 다운로드 (${data.download_filename})
            </a>
        </div>
    ` : '';

    resultCard.innerHTML = `
        <div class="card-header d-flex justify-content-between align-items-center">
            <h6 class="mb-0">
                <i class="fas fa-tag text-info"></i>
                CID: ${data.cid}
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
            ${downloadLinkHtml}
        </div>
    `;
    
    resultsContainer.appendChild(resultCard);
    
    // URL을 안전하게 표시 (HTML 엔티티 변환 방지)
    const urlSpan = resultCard.querySelector('.url-display');
    urlSpan.textContent = data.url;
    
    showResultsSection();
    
    // 결과로 스크롤
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// 계속 버튼 표시
function showContinueButton(nextStep) {
    const nextCidInfo = document.getElementById('nextCidInfo');
    const cidLabels = [
        '원본(1833981)', '1917614', '1829968', '1908612', 
        '1922868', '1776688', '1729890'
    ];
    
    if (nextStep < cidLabels.length) {
        nextCidInfo.textContent = cidLabels[nextStep];
    }
    
    continueSection.style.display = 'block';
    continueSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// 완료 표시
function showComplete() {
    const totalResults = allResults.reduce((sum, result) => sum + result.found_count, 0);
    document.getElementById('totalResults').textContent = totalResults;
    
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
    
    hideAllSections();
    urlInput.value = '';
    urlInput.focus();
    
    // 결과 컨테이너 초기화
    document.getElementById('resultsContainer').innerHTML = '';
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
    document.getElementById('errorText').textContent = message;
    errorMessage.style.display = 'block';
}

function hideError() {
    errorMessage.style.display = 'none';
}

function showResultsSection() {
    resultsSection.style.display = 'block';
}

function hideResultsSection() {
    resultsSection.style.display = 'none';
}

function hideContinueButton() {
    continueSection.style.display = 'none';
}

function hideAllSections() {
    hideProgressSection();
    hideLoading();
    hideError();
    hideResultsSection();
    hideContinueButton();
    completeSection.style.display = 'none';
}