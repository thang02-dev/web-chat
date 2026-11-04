<template>
  <div class="col-12 col-sm-6 col-xl-4 gold-card-col">
    <div class="gold-card" :class="{ 'gold-card-history': !isLatest }">
      <!-- Header thẻ -->
      <div class="gold-card-header">
        <span class="gold-type-badge">{{ card.gold_type }}</span>
        <span v-if="isLatest" class="card-status-pill current-pill">
          <i class="bi bi-lightning-charge-fill me-1"></i>Hiện hành
        </span>
        <span v-else class="card-status-pill history-pill-sm">
          <i class="bi bi-archive me-1"></i>Lịch sử
        </span>
      </div>

      <!-- Body thẻ -->
      <div class="gold-card-body">
        <div class="price-row">
          <!-- Giá Bán Ra -->
          <div class="price-item sell">
            <div class="price-label">
              <i class="bi bi-graph-up-arrow"></i> Giá Bán Ra
            </div>
            <div class="price-value">
              {{ formatVnd(card.sell_price) }}
            </div>
            <!-- Delta so với đợt cũ -->
            <div class="delta-box delta-sell-box">
              <span
                v-if="card.sell_price_delta > 0"
                class="delta-badge delta-up"
              >
                ▲ +{{ formatVnd(card.sell_price_delta) }}
              </span>
              <span
                v-else-if="card.sell_price_delta < 0"
                class="delta-badge delta-down"
              >
                ▼ -{{ formatVnd(Math.abs(card.sell_price_delta)) }}
              </span>
              <span v-else class="delta-badge delta-neutral">
                <i class="bi bi-dash"></i> Không đổi
              </span>
            </div>
          </div>

          <div class="price-divider"></div>

          <!-- Giá Mua Vào -->
          <div class="price-item buy">
            <div class="price-label">
              <i class="bi bi-graph-down-arrow"></i> Giá Mua Vào
            </div>
            <div class="price-value">
              {{ formatVnd(card.buy_price) }}
            </div>
            <!-- Delta so với đợt cũ -->
            <div class="delta-box delta-buy-box">
              <span
                v-if="card.buy_price_delta > 0"
                class="delta-badge delta-up"
              >
                ▲ +{{ formatVnd(card.buy_price_delta) }}
              </span>
              <span
                v-else-if="card.buy_price_delta < 0"
                class="delta-badge delta-down"
              >
                ▼ -{{ formatVnd(Math.abs(card.buy_price_delta)) }}
              </span>
              <span v-else class="delta-badge delta-neutral">
                <i class="bi bi-dash"></i> Không đổi
              </span>
            </div>
          </div>
        </div>

        <!-- Chênh lệch Mua - Bán -->
        <div class="spread-box">
          <div class="spread-inner">
            <span class="spread-label">
              <i class="bi bi-arrows-expand me-1"></i>Chênh lệch Mua - Bán
            </span>
            <span class="spread-value">
              {{ formatVnd(card.spread) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  card: {
    type: Object,
    required: true
  },
  isLatest: {
    type: Boolean,
    default: false
  }
})

function formatVnd(val) {
  if (val === null || val === undefined || isNaN(val)) return '–'
  return Math.abs(Math.round(val)).toLocaleString('vi-VN') + ' đ'
}
</script>
