<template>
  <div v-if="sources.length > 0" class="store-tabs-wrapper">
    <div class="store-tabs-label">
      <i class="bi bi-shop"></i>
      <span>Cửa hàng:</span>
    </div>
    <div class="store-tabs-scroll" role="tablist">
      <button
        v-for="(store, idx) in sources"
        :key="store.id"
        type="button"
        role="tab"
        :aria-selected="selectedId === store.id"
        :class="['store-tab-item', { active: selectedId === store.id }]"
        @click="$emit('select-store', store.id)"
      >
        <span class="store-tab-order">{{ idx + 1 }}</span>
        <span class="store-tab-name">{{ store.name }}</span>
        <span
          v-if="store.last_status === 'SUCCESS'"
          class="store-tab-dot dot-ok"
          title="Lần quét gần nhất: Thành công"
        ></span>
        <span
          v-else-if="store.last_status === 'ERROR'"
          class="store-tab-dot dot-err"
          title="Lần quét gần nhất: Thất bại"
        ></span>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  sources: {
    type: Array,
    default: () => []
  },
  selectedId: {
    type: Number,
    default: null
  }
})

defineEmits(['select-store'])
</script>

<style scoped>
.store-tabs-wrapper {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
  padding: 0.65rem 0.875rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
}

.store-tabs-label {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-muted);
  white-space: nowrap;
  flex-shrink: 0;
}

.store-tabs-scroll {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  overflow-x: auto;
  flex: 1;
  padding-bottom: 2px;
}

.store-tab-item {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.425rem 0.85rem;
  border-radius: var(--radius-sm);
  background-color: var(--bg-sidebar);
  border: 1px solid var(--border);
  color: var(--text-muted);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.12s ease, border-color 0.12s ease, color 0.12s ease;
}

.store-tab-item:hover {
  background-color: var(--bg-hover);
  color: var(--text-main);
}

.store-tab-item.active {
  background-color: var(--accent-soft);
  border-color: var(--accent);
  color: var(--text-main);
  font-weight: 600;
}

.store-tab-order {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--text-muted);
}

.store-tab-item.active .store-tab-order {
  background-color: var(--accent);
  border-color: var(--accent);
  color: var(--on-accent);
}

.store-tab-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}

.store-tab-dot.dot-ok {
  background-color: var(--online);
}

.store-tab-dot.dot-err {
  background-color: var(--danger);
}

@media (max-width: 768px) {
  .store-tabs-wrapper {
    flex-direction: column;
    align-items: stretch;
    gap: 0.5rem;
    padding: 0.55rem 0.75rem;
  }
}
</style>

