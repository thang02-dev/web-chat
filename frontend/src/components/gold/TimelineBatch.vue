<template>
  <div
    class="timeline-batch mb-5"
    :class="{
      'latest-batch': batch.is_latest,
      'history-batch': !batch.is_latest,
      'batch-pulse-highlight': isHighlighted
    }"
  >
    <!-- Batch Header -->
    <div class="batch-header-box mb-3">
      <!-- If Latest -->
      <div
        v-if="batch.is_latest"
        class="d-flex align-items-center justify-content-between flex-wrap gap-2"
      >
        <div class="d-flex align-items-center gap-2">
          <span class="pulse-dot"></span>
          <h3 class="batch-title live-title mb-0">
            Giá Hiện Tại <span class="batch-time-highlight">({{ formatBatchTime(batch) }})</span>
          </h3>
        </div>
        <div class="d-flex align-items-center gap-2">
          <span class="live-indicator">
            <span class="live-dot"></span>LIVE
          </span>
          <button
            type="button"
            class="btn-delete-batch"
            title="Xóa đợt cập nhật này"
            @click.stop="$emit('request-delete', batch)"
          >
            <i class="bi bi-x-lg"></i>
            <span>Xóa</span>
          </button>
        </div>
      </div>

      <!-- If Not Latest (Lịch sử) -->
      <div
        v-else
        class="d-flex align-items-center justify-content-between flex-wrap gap-2"
      >
        <div class="d-flex align-items-center gap-2">
          <span class="history-dot"></span>
          <h3 class="batch-title history-title mb-0">
            {{ formatBatchTime(batch) }}
          </h3>
        </div>
        <div class="d-flex align-items-center gap-2">
          <span class="history-pill">
            <i class="bi bi-arrow-counterclockwise me-1"></i>Đợt cập nhật trước
          </span>
          <button
            type="button"
            class="btn-delete-batch"
            title="Xóa đợt cập nhật này"
            @click.stop="$emit('request-delete', batch)"
          >
            <i class="bi bi-x-lg"></i>
            <span>Xóa</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Batch Cards Grid: mặc định 2 khối, bấm nút để xem tất cả -->
    <div class="row">
      <GoldCard
        v-for="card in visibleCards"
        :key="card.id || card.gold_type"
        :card="card"
        :is-latest="batch.is_latest"
      />
    </div>

    <div v-if="hasMore" class="batch-expand-row">
      <button
        type="button"
        class="btn-expand-batch"
        :aria-expanded="expanded"
        @click="expanded = !expanded"
      >
        <i :class="expanded ? 'bi bi-chevron-up' : 'bi bi-chevron-down'"></i>
        <span>{{ expanded ? 'Thu gọn' : `Xem tất cả (${batch.cards.length})` }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import GoldCard from './GoldCard.vue'

const PREVIEW_COUNT = 2

const props = defineProps({
  batch: {
    type: Object,
    required: true
  },
  isHighlighted: {
    type: Boolean,
    default: false
  }
})

defineEmits(['request-delete'])

const expanded = ref(false)
const cards = computed(() => props.batch?.cards || [])
const hasMore = computed(() => cards.value.length > PREVIEW_COUNT)
const visibleCards = computed(() =>
  expanded.value ? cards.value : cards.value.slice(0, PREVIEW_COUNT)
)

function formatBatchTime(batch) {
  if (!batch) return '–'
  if (batch.batch_time) {
    const d = new Date(batch.batch_time)
    if (!isNaN(d.getTime())) {
      const pad = n => String(n).padStart(2, '0')
      return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())} ${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`
    }
  }
  return batch.formatted_batch_time || '–'
}
</script>

<style scoped>
.batch-expand-row {
  display: flex;
  justify-content: center;
  margin-top: 0.25rem;
}

.btn-expand-batch {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 1.1rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--accent);
  border-radius: var(--radius-sm);
  color: var(--accent);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-expand-batch:hover {
  background-color: var(--accent);
  color: var(--on-accent);
}
</style>

