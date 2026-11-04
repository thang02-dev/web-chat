<template>
  <div v-if="visible" class="gold-modal-backdrop" @click.self="$emit('cancel')">
    <div class="gold-modal-dialog">
      <!-- Modal Header -->
      <div class="gold-modal-header">
        <h4 class="gold-modal-title">
          <i class="bi bi-exclamation-triangle-fill"></i>
          <span>Xác Nhận Xóa Đợt Giá</span>
        </h4>
        <button
          type="button"
          class="gold-modal-close"
          @click="$emit('cancel')"
          :disabled="loading"
        >
          <i class="bi bi-x-lg"></i>
        </button>
      </div>

      <!-- Modal Body -->
      <div class="gold-modal-body">
        <p class="mb-2">
          Bạn có chắc chắn muốn xóa dữ liệu giá vàng của đợt cập nhật này không?
        </p>

        <div v-if="batch" class="gold-modal-batch-info">
          <div class="d-flex align-items-center justify-content-between mb-2">
            <span class="text-secondary small">Mốc thời gian:</span>
            <strong class="text-gold" style="font-family: monospace; font-size: 0.95rem;">
              {{ formatBatchTime(batch) }}
            </strong>
          </div>
          <div class="d-flex align-items-center justify-content-between">
            <span class="text-secondary small">Số lượng bản ghi:</span>
            <span class="badge bg-secondary">{{ batch.cards?.length || 0 }} loại vàng</span>
          </div>

          <div v-if="batch.cards?.length" class="gold-modal-cards-list">
            <span
              v-for="c in batch.cards"
              :key="c.id || c.gold_type"
              class="gold-modal-card-pill"
            >
              {{ c.gold_type }}
            </span>
          </div>
        </div>

        <div class="gold-modal-warning">
          <i class="bi bi-shield-exclamation fs-5 flex-shrink-0"></i>
          <div>
            <strong>Lưu ý:</strong> Hành động này sẽ xóa vĩnh viễn các bản ghi trên cơ sở dữ liệu và tự động cập nhật lại dòng thời gian cho toàn bộ người dùng đang theo dõi.
          </div>
        </div>
      </div>

      <!-- Modal Footer -->
      <div class="gold-modal-footer">
        <button
          type="button"
          class="btn-modal-cancel"
          @click="$emit('cancel')"
          :disabled="loading"
        >
          Hủy bỏ
        </button>
        <button
          type="button"
          class="btn-modal-delete"
          @click="$emit('confirm')"
          :disabled="loading"
        >
          <span
            v-if="loading"
            class="spinner-border spinner-border-sm me-1"
            role="status"
          ></span>
          <i v-else class="bi bi-trash3-fill me-1"></i>
          {{ loading ? 'Đang xóa...' : 'Xác nhận xóa' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  batch: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['cancel', 'confirm'])

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

