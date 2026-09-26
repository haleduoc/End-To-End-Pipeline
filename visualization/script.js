/* INJECT_SELLERS */
/* INJECT_PRODUCTS */

// Safe fallback if not injected
const sellersData = (typeof SELLERS !== 'undefined' && Array.isArray(SELLERS)) ? SELLERS : [];
const productsData = (typeof PRODUCTS !== 'undefined' && Array.isArray(PRODUCTS)) ? PRODUCTS : [];

// Utility: Format Vietnamese Currency
function formatVND(val) {
  if (val == null || isNaN(val)) return '0 ₫';
  return Math.round(Number(val)).toLocaleString('vi-VN') + ' ₫';
}

function formatNumber(val) {
  if (val == null || isNaN(val)) return '0';
  return Math.round(Number(val)).toLocaleString('vi-VN');
}

function formatStars(rating) {
  const r = Math.round(Number(rating) || 0);
  const full = Math.min(5, Math.max(0, r));
  const empty = 5 - full;
  return '★'.repeat(full) + '☆'.repeat(empty);
}

// 1. SECTION 1: Header summary
function initHeader() {
  const totalProds = productsData.length;
  const uniqueSellers = new Set(productsData.map(p => p.seller_name).filter(Boolean)).size;
  const summaryEl = document.getElementById('headerSummaryText');
  if (summaryEl) {
    summaryEl.textContent = `${formatNumber(totalProds)} products · ${formatNumber(uniqueSellers)} sellers`;
  }
}

// 2. SECTION 2: KPI Bar computation
function initKPI() {
  const totalProds = productsData.length;
  const uniqueSellers = new Set(productsData.map(p => p.seller_name).filter(Boolean)).size;

  let sumPrice = 0;
  let sumRating = 0;
  let sumDiscount = 0;

  productsData.forEach(p => {
    sumPrice += Number(p.price) || 0;
    sumRating += Number(p.rating_average) || 0;
    sumDiscount += Number(p.discount_rate) || 0;
  });

  const avgPrice = totalProds > 0 ? (sumPrice / totalProds) : 0;
  const avgRating = totalProds > 0 ? (sumRating / totalProds) : 0;
  const avgDiscount = totalProds > 0 ? (sumDiscount / totalProds) : 0;

  document.getElementById('kpiTotalProducts').textContent = formatNumber(totalProds);
  document.getElementById('kpiTotalSellers').textContent = formatNumber(uniqueSellers);
  document.getElementById('kpiAvgPrice').textContent = formatVND(avgPrice);
  document.getElementById('kpiAvgRating').textContent = `${avgRating.toFixed(1)} ★`;
  document.getElementById('kpiAvgDiscount').textContent = `${avgDiscount.toFixed(1)}%`;
}

// 3. SECTION 3: Charts Row
// Left: Inline SVG Bar Chart (Top 10 Sellers)
function initSvgSellerChart() {
  const wrapper = document.getElementById('svgChartWrapper');
  if (!wrapper) return;

  const topSellers = sellersData
    .slice()
    .sort((a, b) => (Number(b.total_products) || 0) - (Number(a.total_products) || 0))
    .slice(0, 10);

  if (topSellers.length === 0) {
    wrapper.innerHTML = '<p style="color: #6b7280; font-size: 0.9rem; padding: 20px;">Không có dữ liệu người bán.</p>';
    return;
  }

  const maxVal = Math.max(...topSellers.map(s => Number(s.total_products) || 0), 1);
  const chartHeight = topSellers.length * 36 + 24;
  const barHeight = 26;
  const labelWidth = 190;
  const maxBarWidth = 330;

  let svgContent = `
    <svg width="100%" height="${chartHeight}" viewBox="0 0 620 ${chartHeight}" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="barTealGrad" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#4db6ac"/>
          <stop offset="100%" stop-color="#00897b"/>
        </linearGradient>
      </defs>
  `;

  topSellers.forEach((s, idx) => {
    const y = 14 + idx * 36;
    const count = Number(s.total_products) || 0;
    const barWidth = Math.max(8, (count / maxVal) * maxBarWidth);
    const rawName = s.seller_name || 'Unknown';
    const truncatedName = rawName.length > 22 ? rawName.slice(0, 20) + '...' : rawName;

    // Y Axis Label
    svgContent += `
      <text x="${labelWidth - 12}" y="${y + 18}" 
            text-anchor="end" 
            fill="#1a1a2e" 
            font-size="12px" 
            font-weight="500">
        ${truncatedName}
      </text>
    `;

    // Horizontal Bar
    svgContent += `
      <rect x="${labelWidth}" y="${y}" 
            width="${barWidth}" height="${barHeight}" 
            rx="5" fill="url(#barTealGrad)" />
    `;

    // Bar Value Label
    svgContent += `
      <text x="${labelWidth + barWidth + 8}" y="${y + 18}" 
            fill="#00897b" 
            font-size="12px" 
            font-weight="700">
        ${count}
      </text>
    `;
  });

  svgContent += `</svg>`;
  wrapper.innerHTML = svgContent;
}

// Right: Chart.js Histogram (Price Distribution)
function initPriceHistogram() {
  const canvas = document.getElementById('priceHistogramChart');
  if (!canvas) return;

  const buckets = {
    '<100k': 0,
    '100k-500k': 0,
    '500k-1M': 0,
    '1M-5M': 0,
    '>5M': 0
  };

  productsData.forEach(p => {
    const price = Number(p.price) || 0;
    if (price < 100000) {
      buckets['<100k']++;
    } else if (price < 500000) {
      buckets['100k-500k']++;
    } else if (price < 1000000) {
      buckets['500k-1M']++;
    } else if (price < 5000000) {
      buckets['1M-5M']++;
    } else {
      buckets['>5M']++;
    }
  });

  const ctx = canvas.getContext('2d');
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['<100k', '100k-500k', '500k-1M', '1M-5M', '>5M'],
      datasets: [{
        label: 'Số lượng sản phẩm',
        data: Object.values(buckets),
        backgroundColor: '#4db6ac',
        hoverBackgroundColor: '#00897b',
        borderRadius: 8,
        barPercentage: 0.65
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.parsed.y} sản phẩm`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#6b7280', font: { family: 'Inter', size: 12 } }
        },
        y: {
          grid: { color: 'rgba(226, 232, 240, 0.7)' },
          ticks: { precision: 0, color: '#6b7280', font: { family: 'Inter', size: 12 } }
        }
      }
    }
  });
}

// 4. SECTION 4: Seller Cards Grid
function initSellerCards() {
  const grid = document.getElementById('sellersGrid');
  const countSubtext = document.getElementById('sellerCountSubtext');
  if (!grid) return;

  if (countSubtext) {
    countSubtext.textContent = `Tổng cộng ${sellersData.length} nhà bán hàng`;
  }

  if (sellersData.length === 0) {
    grid.innerHTML = '<p style="color: #6b7280; font-size: 0.9rem;">Chưa có dữ liệu người bán.</p>';
    return;
  }

  let html = '';
  sellersData.forEach(seller => {
    const sName = seller.seller_name || 'Unknown';
    const totalProd = Number(seller.total_products) || 0;
    const avgP = Number(seller.avg_price) || 0;
    const minP = Number(seller.min_price) || 0;
    const maxP = Number(seller.max_price) || 0;
    const avgR = Number(seller.avg_rating) || 0;
    const totalRev = Number(seller.total_reviews) || 0;

    const ratingPercent = Math.min(100, Math.max(0, (avgR / 5) * 100));
    let barColor = '#ef4444'; // Red < 3.0
    if (avgR >= 4.0) {
      barColor = '#22c55e'; // Green >= 4.0
    } else if (avgR >= 3.0) {
      barColor = '#f59e0b'; // Amber 3.0 - 3.9
    }

    html += `
      <div class="seller-card">
        <div class="seller-header">
          <h3 class="seller-name" title="${sName}">${sName}</h3>
          <span class="seller-badge">${totalProd} sp</span>
        </div>
        <div class="seller-price-row">
          <span>Avg: <strong>${formatVND(avgP)}</strong></span>
          <span>${formatVND(minP)} – ${formatVND(maxP)}</span>
        </div>
        <div class="seller-rating-section">
          <div class="rating-track">
            <div class="rating-bar-fill" style="width: ${ratingPercent}%; background-color: ${barColor};"></div>
          </div>
          <div class="rating-subtext">
            ${avgR.toFixed(1)} ★ · ${formatNumber(totalRev)} reviews
          </div>
        </div>
      </div>
    `;
  });

  grid.innerHTML = html;
}

// 5. SECTION 5: Product Table with Filter & Pagination
let currentFilteredProducts = [];
let currentPage = 1;
const PAGE_SIZE = 10;
const pageSize = PAGE_SIZE;

function initProductTable() {
  currentFilteredProducts = productsData.slice();

  // Populate Seller Dropdown
  const sellerSelect = document.getElementById('filterSeller');
  if (sellerSelect) {
    const uniqueSellers = Array.from(new Set(productsData.map(p => p.seller_name).filter(Boolean))).sort();
    uniqueSellers.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s;
      opt.textContent = s;
      sellerSelect.appendChild(opt);
    });
  }

  // Event Listeners
  const searchInput = document.getElementById('filterSearch');
  const ratingSelect = document.getElementById('filterRating');
  const btnPrev = document.getElementById('btnPrevPage');
  const btnNext = document.getElementById('btnNextPage');
  const btnExport = document.getElementById('btnExportCsv');

  function applyFilters() {
    const query = (searchInput.value || '').trim().toLowerCase();
    const selectedSeller = sellerSelect.value;
    const minRating = Number(ratingSelect.value) || 0;

    currentFilteredProducts = productsData.filter(p => {
      const matchesName = !query || (p.product_name && p.product_name.toLowerCase().includes(query));
      const matchesSeller = !selectedSeller || p.seller_name === selectedSeller;
      const matchesRating = (Number(p.rating_average) || 0) >= minRating;
      return matchesName && matchesSeller && matchesRating;
    });

    currentPage = 1;
    renderTable();
  }

  if (searchInput) searchInput.addEventListener('input', applyFilters);
  if (sellerSelect) sellerSelect.addEventListener('change', applyFilters);
  if (ratingSelect) ratingSelect.addEventListener('change', applyFilters);

  if (btnPrev) {
    btnPrev.addEventListener('click', () => {
      if (currentPage > 1) {
        currentPage--;
        renderTable();
      }
    });
  }

  if (btnNext) {
    btnNext.addEventListener('click', () => {
      const totalPages = Math.ceil(currentFilteredProducts.length / pageSize) || 1;
      if (currentPage < totalPages) {
        currentPage++;
        renderTable();
      }
    });
  }

  if (btnExport) {
    btnExport.addEventListener('click', exportToCsv);
  }

  renderTable();
}

function renderTable() {
  const tbody = document.getElementById('productTableBody');
  const pageInfo = document.getElementById('paginationInfo');
  const pageNum = document.getElementById('currentPageNum');
  const btnPrev = document.getElementById('btnPrevPage');
  const btnNext = document.getElementById('btnNextPage');

  if (!tbody) return;

  const total = currentFilteredProducts.length;
  const totalPages = Math.ceil(total / pageSize) || 1;
  currentPage = Math.max(1, Math.min(currentPage, totalPages));

  const startIdx = total === 0 ? 0 : (currentPage - 1) * pageSize;
  const endIdx = Math.min(startIdx + pageSize, total);
  const pageRows = currentFilteredProducts.slice(startIdx, endIdx);

  if (pageRows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: #6b7280; padding: 28px;">Không tìm thấy sản phẩm phù hợp.</td></tr>`;
  } else {
    let rowsHtml = '';
    pageRows.forEach(prod => {
      const name = prod.product_name || 'N/A';
      const price = Number(prod.price) || 0;
      const origPrice = Number(prod.original_price) || 0;
      const discount = Number(prod.discount_rate) || 0;
      const rating = Number(prod.rating_average) || 0;
      const reviews = Number(prod.review_count) || 0;
      const seller = prod.seller_name || 'Unknown';

      const discountClass = discount > 0 ? 'discount-active' : 'discount-zero';
      const discountText = discount > 0 ? `-${discount}%` : '0%';

      rowsHtml += `
        <tr>
          <td class="product-name-cell" title="${name}">${name}</td>
          <td><strong>${formatVND(price)}</strong></td>
          <td style="color: #6b7280; text-decoration: ${discount > 0 ? 'line-through' : 'none'};">${formatVND(origPrice)}</td>
          <td class="discount-tag ${discountClass}">${discountText}</td>
          <td class="star-rating-cell" title="${rating.toFixed(1)} ★">${formatStars(rating)} <span style="font-size: 0.78rem; color: #6b7280;">(${rating.toFixed(1)})</span></td>
          <td>${formatNumber(reviews)}</td>
          <td style="color: #4b5563;">${seller}</td>
        </tr>
      `;
    });
    tbody.innerHTML = rowsHtml;
  }

  // Update Pagination Controls
  if (pageInfo) {
    const displayStart = total === 0 ? 0 : startIdx + 1;
    pageInfo.textContent = `Showing ${displayStart}–${endIdx} of ${total} products`;
  }
  if (pageNum) pageNum.textContent = currentPage;
  if (btnPrev) btnPrev.disabled = (currentPage <= 1);
  if (btnNext) btnNext.disabled = (currentPage >= totalPages || total === 0);
}

// Export CSV handler
function exportToCsv() {
  if (currentFilteredProducts.length === 0) {
    alert('Không có dữ liệu để xuất CSV.');
    return;
  }

  const headers = ['Product ID', 'Product Name', 'Price', 'Original Price', 'Discount Rate', 'Rating Average', 'Review Count', 'Seller Name'];
  const csvRows = [];
  csvRows.push(headers.join(','));

  currentFilteredProducts.forEach(p => {
    const escapeCsv = (str) => `"${String(str || '').replace(/"/g, '""')}"`;
    const row = [
      p.product_id || '',
      escapeCsv(p.product_name),
      p.price || 0,
      p.original_price || 0,
      p.discount_rate || 0,
      p.rating_average || 0,
      p.review_count || 0,
      escapeCsv(p.seller_name)
    ];
    csvRows.push(row.join(','));
  });

  const csvString = '\uFEFF' + csvRows.join('\n'); // UTF-8 BOM
  const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', 'tiki_products.csv');
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// Document Ready Initialization
document.addEventListener('DOMContentLoaded', () => {
  initHeader();
  initKPI();
  initSvgSellerChart();
  initPriceHistogram();
  initSellerCards();
  initProductTable();
});
