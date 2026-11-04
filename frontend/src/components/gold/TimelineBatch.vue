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

    <!-- Batch Cards Grid -->
    <div class="row">
      <GoldCard
        v-for="card in batch.cards"
        :key="card.id || card.gold_type"
        :card="card"
        :is-latest="batch.is_latest"
      />
    </div>
  </div>
</template>

<script setup>
import GoldCard from './GoldCard.vue'

defineProps({
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

