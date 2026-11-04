<template>
  <div v-if="visible" class="toast-container">
    <div class="toast-card">
      <i
        class="bi fs-5"
        :class="{
          'bi-check-circle-fill text-success': type === 'success',
          'bi-exclamation-triangle-fill text-danger': type === 'danger',
          'bi-broadcast text-gold': type === 'info'
        }"
      ></i>
      <span class="small fw-semibold">{{ message }}</span>
      <button
        type="button"
        class="toast-btn-close"
        aria-label="Close"
        @click="$emit('close')"
      >
        &times;
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  message: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'info' // 'success', 'danger', 'info'
  }
})

defineEmits(['close'])
</script>

