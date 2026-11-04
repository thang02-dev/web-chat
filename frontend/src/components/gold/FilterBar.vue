<template>
  <div class="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
    <div>
      <h2 class="dashboard-heading mb-1">
        <i class="bi bi-clock-history text-gold me-2"></i>Dòng Thời Gian Biến Động Giá
      </h2>
      <p class="text-secondary small mb-0">Theo dõi chi tiết từng đợt cập nhật và so sánh biến động giá</p>
    </div>

    <!-- Filter form -->
    <div class="d-flex align-items-center gap-2">
      <label for="typeFilter" class="filter-label">
        <i class="bi bi-funnel me-1"></i>Lọc theo loại:
      </label>
      <select
        id="typeFilter"
        class="filter-select"
        :value="selectedType"
        @change="$emit('update:selectedType', $event.target.value)"
      >
        <option value="ALL">Tất cả</option>
        <option
          v-for="item in goldTypes"
          :key="item"
          :value="item"
        >
          {{ item }}
        </option>
      </select>
    </div>
  </div>
</template>

<script setup>
defineProps({
  goldTypes: {
    type: Array,
    default: () => []
  },
  selectedType: {
    type: String,
    default: 'ALL'
  }
})

defineEmits(['update:selectedType'])
</script>
