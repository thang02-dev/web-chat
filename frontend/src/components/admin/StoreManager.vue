<template>
  <div class="store-manager">
    <!-- Toolbar -->
    <div class="store-toolbar">
      <div class="toolbar-info">
        <h3>Danh sách cửa hàng quét giá vàng</h3>
        <p>
          Kéo thả biểu tượng <i class="bi bi-grip-vertical"></i> để sắp xếp thứ tự hiển thị trên trang Giá vàng (cửa hàng đầu tiên sẽ là mặc định).
        </p>
      </div>

      <div class="toolbar-actions">
        <button
          type="button"
          class="btn btn-secondary"
          :disabled="loading"
          title="Tải lại danh sách cửa hàng"
          @click="loadStores"
        >
          <i class="bi bi-arrow-clockwise"></i>
          <span>Làm mới</span>
        </button>

        <button
          type="button"
          class="btn btn-primary btn-add-store"
          @click="openCreateModal"
        >
          <i class="bi bi-plus-lg"></i>
          <span>Thêm cửa hàng</span>
        </button>
      </div>
    </div>

    <!-- Thanh đặt nhanh chu kỳ quét cho tất cả cửa hàng -->
    <div v-if="stores.length > 0" class="bulk-interval-bar">
      <div class="bulk-interval-label">
        <i class="bi bi-clock-history"></i>
        <span>Chu kỳ quét cho tất cả:</span>
      </div>

      <div class="bulk-interval-controls">
        <div class="bulk-preset-pills">
          <button
            v-for="p in [1, 5, 10, 15, 30, 60]"
            :key="p"
            type="button"
            :class="['bulk-pill-btn', { active: bulkInterval === p }]"
            @click="bulkInterval = p"
          >
            {{ p }}p
          </button>
        </div>

        <div class="bulk-input-group">
          <input
            v-model.number="bulkInterval"
            type="number"
            min="1"
            max="1440"
            class="bulk-number-input"
            aria-label="Số phút quét cho tất cả cửa hàng"
          />
          <span class="bulk-unit">phút</span>
        </div>

        <button
          type="button"
          class="btn btn-secondary btn-apply-bulk"
          :disabled="applyingBulk || !bulkInterval || bulkInterval < 1 || bulkInterval > 1440"
          @click="handleApplyBulkInterval"
        >
          <span v-if="applyingBulk" class="spinner-inline"></span>
          <i v-else class="bi bi-check2-all"></i>
          <span>Áp dụng tất cả</span>
        </button>
      </div>
    </div>

    <!-- Table Container -->
    <div class="store-table-card">
      <div v-if="loading && stores.length === 0" class="store-empty-state">
        <p>Đang tải danh sách cửa hàng...</p>
      </div>

      <div v-else-if="stores.length === 0" class="store-empty-state">
        <i class="bi bi-shop empty-store-icon"></i>
        <p>Chưa có cửa hàng nào trong danh sách. Nhấn "Thêm cửa hàng" để bắt đầu.</p>
      </div>

      <div v-else class="store-table-scroll">
        <table class="store-table">
          <thead>
            <tr>
              <th class="col-drag" title="Kéo thả sắp xếp"></th>
              <th class="col-order">Thứ tự</th>
              <th>Tên cửa hàng</th>
              <th>Link trang web</th>
              <th>Thời gian quét</th>
              <th>Trạng thái quét</th>
              <th>Tự động</th>
              <th class="text-right">Thao tác</th>
            </tr>
          </thead>

          <tbody ref="tbodyRef">
            <tr
              v-for="(store, idx) in stores"
              :key="store.id"
              :data-id="store.id"
              class="store-row"
              draggable="true"
              @dragstart="onNativeDragStart(idx, $event)"
              @dragover.prevent
              @drop="onNativeDrop(idx)"
            >
              <td class="col-drag">
                <button
                  type="button"
                  class="drag-handle"
                  title="Kéo thả để đổi thứ tự cửa hàng"
                  aria-label="Kéo thả để đổi thứ tự cửa hàng"
                >
                  <i class="bi bi-grip-vertical"></i>
                </button>
              </td>

              <td class="col-order">
                <span :class="['order-pill', { 'is-default': idx === 0 }]">
                  #{{ idx + 1 }}
                  <span v-if="idx === 0" class="default-tag">Mặc định</span>
                </span>
              </td>

              <td>
                <div class="store-name-cell">
                  <span class="store-name-text">{{ store.name }}</span>
                  <span v-if="store.extract_rules?.mode === 'CSS'" class="rule-tag" title="Sử dụng CSS Selector tùy chỉnh">
                    CSS
                  </span>
                </div>
              </td>

              <td>
                <a
                  :href="store.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="store-url-link"
                  :title="store.url"
                >
                  <span>{{ formatShortUrl(store.url) }}</span>
                  <i class="bi bi-box-arrow-up-right"></i>
                </a>
              </td>

              <td>
                <span class="interval-badge">
                  <i class="bi bi-clock"></i>
                  <span>{{ store.interval_minutes }} phút / lần</span>
                </span>
              </td>

              <td>
                <div class="scan-status-cell" :title="buildStatusTooltip(store)">
                  <span
                    v-if="store.last_status === 'SUCCESS'"
                    class="scan-status-badge status-success"
                  >
                    <i class="bi bi-check-circle-fill"></i>
                    <span>Thành công</span>
                  </span>
                  <span
                    v-else-if="store.last_status === 'ERROR'"
                    class="scan-status-badge status-error"
                  >
                    <i class="bi bi-exclamation-triangle-fill"></i>
                    <span>Thất bại</span>
                  </span>
                  <span v-else class="scan-status-badge status-never">
                    <i class="bi bi-dash-circle"></i>
                    <span>Chưa quét</span>
                  </span>

                  <span v-if="store.last_message" class="scan-status-sub">
                    {{ store.last_message }}
                  </span>
                  <span v-if="store.last_scan_at" class="scan-status-time">
                    {{ formatTime(store.last_scan_at) }}
                  </span>
                </div>
              </td>

              <td>
                <label class="switch" :title="store.is_enabled ? 'Đang bật quét tự động' : 'Đang tắt quét tự động'">
                  <input
                    type="checkbox"
                    :checked="store.is_enabled"
                    @change="handleToggleEnabled(store, $event.target.checked)"
                  />
                  <span class="slider"></span>
                </label>
              </td>

              <td class="text-right">
                <div class="row-actions">
                  <button
                    type="button"
                    class="btn-row-action btn-test"
                    :disabled="testingId === store.id"
                    title="Quét thử bảng giá (chỉ kiểm tra, không lưu dữ liệu)"
                    @click="handleTestSaved(store)"
                  >
                    <span v-if="testingId === store.id" class="spinner-inline"></span>
                    <i v-else class="bi bi-radar"></i>
                    <span>{{ testingId === store.id ? 'Đang thử...' : 'Quét thử' }}</span>
                  </button>

                  <button
                    type="button"
                    class="btn-row-action btn-edit"
                    title="Chỉnh sửa cửa hàng"
                    @click="openEditModal(store)"
                  >
                    <i class="bi bi-pencil"></i>
                    <span>Sửa</span>
                  </button>

                  <button
                    type="button"
                    class="btn-row-action btn-del"
                    title="Xóa cửa hàng"
                    @click="openDeleteModal(store)"
                  >
                    <i class="bi bi-trash"></i>
                    <span>Xóa</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Thêm / Sửa Cửa Hàng -->
    <div v-if="formModal.open" class="modal-backdrop" @click.self="closeFormModal">
      <div class="modal-card modal-wide">
        <div class="modal-header">
          <h3>{{ formModal.isEdit ? 'Chỉnh sửa cửa hàng giá vàng' : 'Thêm cửa hàng giá vàng mới' }}</h3>
          <button
            type="button"
            class="close-btn"
            title="Đóng"
            aria-label="Đóng"
            @click="closeFormModal"
          >
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <form class="modal-body form-stack" @submit.prevent="handleSubmitForm">
          <div v-if="formModal.error" class="form-error-alert" role="alert">
            {{ formModal.error }}
          </div>

          <div class="form-group">
            <label for="storeNameInput">Tên cửa hàng / trang web</label>
            <input
              id="storeNameInput"
              v-model="form.name"
              type="text"
              required
              maxlength="100"
              class="input-field"
              placeholder="Ví dụ: Ngọc Thịnh Jewelry, Hiệu Vàng Trữ..."
            />
          </div>

          <div class="form-group">
            <label for="storeUrlInput">Link trang web</label>
            <input
              id="storeUrlInput"
              v-model="form.url"
              type="url"
              required
              class="input-field"
              placeholder="https://ngocthinh-jewelry.vn/"
            />
          </div>

          <div class="form-row-2">
            <div class="form-group">
              <label for="storeIntervalInput">Thời gian quét định kỳ (phút / lần)</label>
              <div class="interval-input-group">
                <input
                  id="storeIntervalInput"
                  v-model.number="form.interval_minutes"
                  type="number"
                  min="1"
                  max="1440"
                  required
                  class="input-field"
                />
                <div class="preset-chips">
                  <button
                    v-for="p in [1, 5, 10, 15, 30, 60]"
                    :key="p"
                    type="button"
                    :class="['preset-chip', { active: form.interval_minutes === p }]"
                    @click="form.interval_minutes = p"
                  >
                    {{ p }}p
                  </button>
                </div>
              </div>
            </div>

            <div class="form-group">
              <label>Trạng thái quét tự động</label>
              <label class="checkbox-inline">
                <input v-model="form.is_enabled" type="checkbox" />
                <span>Kích hoạt tự động quét theo chu kỳ</span>
              </label>
            </div>
          </div>

          <!-- Cấu hình nâng cao (Link bảng giá riêng & Luật CSS) -->
          <div class="advanced-box">
            <button
              type="button"
              class="advanced-toggle-btn"
              @click="formModal.showAdvanced = !formModal.showAdvanced"
            >
              <i :class="formModal.showAdvanced ? 'bi bi-chevron-down' : 'bi bi-chevron-right'"></i>
              <span>Cấu hình nâng cao (Link bảng giá riêng / CSS Selector tùy chỉnh)</span>
            </button>

            <div v-if="formModal.showAdvanced" class="advanced-body">
              <div class="form-group">
                <label for="priceUrlInput">Link bảng giá riêng (tùy chọn, nếu bảng giá nằm ở trang hoặc endpoint con)</label>
                <input
                  id="priceUrlInput"
                  v-model="form.extract_rules.price_url"
                  type="text"
                  class="input-field"
                  placeholder="Ví dụ: /layout/load_bang_gia.php hoặc để trống để tự dò"
                />
              </div>

              <div class="form-group">
                <label>Chế độ bóc tách bảng giá</label>
                <div class="mode-radios">
                  <label class="radio-label">
                    <input v-model="form.extract_rules.mode" type="radio" value="AUTO" />
                    <span>Tự động nhận dạng (Bảng HTML, Lưới Div, AJAX)</span>
                  </label>
                  <label class="radio-label">
                    <input v-model="form.extract_rules.mode" type="radio" value="CSS" />
                    <span>Chỉ định CSS Selector tùy chỉnh</span>
                  </label>
                </div>
              </div>

              <div v-if="form.extract_rules.mode === 'CSS'" class="css-rules-grid">
                <div class="form-group">
                  <label>Selector từng dòng (Row Selector)</label>
                  <input
                    v-model="form.extract_rules.row_selector"
                    type="text"
                    class="input-field"
                    placeholder="Ví dụ: .contenttogoldflex > div hoặc table tbody tr"
                  />
                </div>
                <div class="form-group">
                  <label>Selector tên loại vàng</label>
                  <input
                    v-model="form.extract_rules.name_selector"
                    type="text"
                    class="input-field"
                    placeholder="Ví dụ: .headerindex1 hoặc td:nth-child(1)"
                  />
                </div>
                <div class="form-group">
                  <label>Selector giá Mua vào</label>
                  <input
                    v-model="form.extract_rules.buy_selector"
                    type="text"
                    class="input-field"
                    placeholder="Ví dụ: .headerindex2 hoặc td:nth-child(2)"
                  />
                </div>
                <div class="form-group">
                  <label>Selector giá Bán ra</label>
                  <input
                    v-model="form.extract_rules.sell_selector"
                    type="text"
                    class="input-field"
                    placeholder="Ví dụ: .headerindex3 hoặc td:nth-child(3)"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Kết quả Quét thử trực tiếp trong Form -->
          <div v-if="draftTestResult" class="test-result-box" :class="draftTestResult.success ? 'box-ok' : 'box-err'">
            <div class="test-result-header">
              <span class="test-result-title">
                <i :class="draftTestResult.success ? 'bi bi-check-circle-fill' : 'bi bi-exclamation-triangle-fill'"></i>
                <span>{{ draftTestResult.message }}</span>
              </span>
              <span v-if="draftTestResult.strategy" class="test-meta-tag">
                Chiến lược: {{ draftTestResult.strategy }} · {{ draftTestResult.duration_ms }}ms
              </span>
            </div>

            <div v-if="draftTestResult.preview?.length > 0" class="preview-table-wrap">
              <table class="preview-table">
                <thead>
                  <tr>
                    <th>Loại vàng</th>
                    <th>Giá mua vào</th>
                    <th>Giá bán ra</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, rIdx) in draftTestResult.preview.slice(0, 8)" :key="rIdx">
                    <td>{{ row.gold_type }}</td>
                    <td>{{ formatVnd(row.buy_price) }}</td>
                    <td>{{ formatVnd(row.sell_price) }}</td>
                  </tr>
                </tbody>
              </table>
              <p class="preview-note">Dữ liệu quét thử chỉ để kiểm tra, không lưu vào cơ sở dữ liệu.</p>
            </div>
          </div>

          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary"
              :disabled="testingDraft || !form.url.trim()"
              @click="handleTestDraft"
            >
              <span v-if="testingDraft" class="spinner-inline"></span>
              <i v-else class="bi bi-radar"></i>
              <span>{{ testingDraft ? 'Đang quét thử...' : 'Quét thử link này' }}</span>
            </button>

            <div class="footer-right">
              <button type="button" class="btn btn-secondary" @click="closeFormModal">
                Hủy bỏ
              </button>
              <button type="submit" class="btn btn-primary" :disabled="savingForm">
                <span v-if="savingForm" class="spinner-inline"></span>
                <span>{{ formModal.isEdit ? 'Lưu thay đổi' : 'Thêm cửa hàng' }}</span>
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Kết Quả Quét Thử Từ Bảng -->
    <div v-if="testModal.open" class="modal-backdrop" @click.self="testModal.open = false">
      <div class="modal-card modal-wide">
        <div class="modal-header">
          <h3>Kết quả quét thử: {{ testModal.storeName }}</h3>
          <button
            type="button"
            class="close-btn"
            title="Đóng"
            aria-label="Đóng"
            @click="testModal.open = false"
          >
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <div class="modal-body" v-if="testModal.result">
          <div :class="['test-summary-banner', testModal.result.success ? 'banner-ok' : 'banner-err']">
            <div class="banner-main">
              <i :class="testModal.result.success ? 'bi bi-check-circle-fill' : 'bi bi-exclamation-triangle-fill'"></i>
              <strong>{{ testModal.result.success ? 'Thành công' : 'Thất bại' }}:</strong>
              <span>{{ testModal.result.message }}</span>
            </div>
            <div class="banner-sub">
              <span>Chiến lược: <b>{{ testModal.result.strategy || 'NONE' }}</b></span>
              <span>Thời gian phản hồi: <b>{{ testModal.result.duration_ms }}ms</b></span>
              <span v-if="testModal.result.price_date">Ngày giá: <b>{{ testModal.result.price_date }}</b></span>
            </div>
          </div>

          <div v-if="testModal.result.preview?.length > 0" class="preview-table-wrap">
            <table class="preview-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Loại vàng</th>
                  <th>Giá mua vào</th>
                  <th>Giá bán ra</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in testModal.result.preview" :key="idx">
                  <td>{{ idx + 1 }}</td>
                  <td><strong>{{ item.gold_type }}</strong></td>
                  <td class="text-buy">{{ formatVnd(item.buy_price) }}</td>
                  <td class="text-sell">{{ formatVnd(item.sell_price) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <p class="preview-note">
            Lưu ý: Quét thử chỉ kiểm tra khả năng lấy bảng giá và cập nhật cột trạng thái quét, không lưu dữ liệu giá vào lịch sử.
          </p>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-primary" @click="testModal.open = false">
            Đóng
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Xác Nhận Xóa Cửa Hàng -->
    <div v-if="deleteModal.open" class="modal-backdrop" @click.self="deleteModal.open = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3 class="text-danger">Xác nhận xóa cửa hàng</h3>
          <button
            type="button"
            class="close-btn"
            title="Đóng"
            aria-label="Đóng"
            @click="deleteModal.open = false"
          >
            <i class="bi bi-x-lg"></i>
          </button>
        </div>

        <div class="modal-body">
          <p>
            Bạn có chắc chắn muốn xóa cửa hàng
            <strong>{{ deleteModal.store?.name }}</strong>
            ({{ deleteModal.store?.url }}) không?
          </p>
          <p class="delete-warning-box">
            <strong>Cảnh báo:</strong> Hành động này sẽ xóa vĩnh viễn cửa hàng cùng
            <strong>{{ deleteModal.historyCount }}</strong> bản ghi lịch sử giá vàng của cửa hàng này.
          </p>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" @click="deleteModal.open = false">
            Hủy bỏ
          </button>
          <button
            type="button"
            class="btn btn-danger"
            :disabled="deleteModal.deleting"
            @click="confirmDeleteStore"
          >
            <span v-if="deleteModal.deleting" class="spinner-inline"></span>
            <i v-else class="bi bi-trash"></i>
            <span>Xóa cửa hàng</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import Sortable from 'sortablejs'
import goldSourcesApi from '@/services/goldSources'

const emit = defineEmits(['toast', 'count-change', 'interval-all-changed'])

const stores = ref([])
const loading = ref(false)
const testingId = ref(null)
const bulkInterval = ref(10)
const applyingBulk = ref(false)
const tbodyRef = ref(null)
let sortableInstance = null
let draggedIdx = null

const formModal = reactive({
  open: false,
  isEdit: false,
  editId: null,
  showAdvanced: false,
  error: ''
})

const form = reactive({
  name: '',
  url: '',
  interval_minutes: 10,
  is_enabled: true,
  extract_rules: {
    mode: 'AUTO',
    price_url: '',
    row_selector: '',
    name_selector: '',
    buy_selector: '',
    sell_selector: '',
    column_order: 'BUY_SELL'
  }
})

const savingForm = ref(false)
const testingDraft = ref(false)
const draftTestResult = ref(null)

const testModal = reactive({
  open: false,
  storeName: '',
  result: null
})

const deleteModal = reactive({
  open: false,
  store: null,
  historyCount: 0,
  deleting: false
})

watch(
  () => stores.value.length,
  (cnt) => emit('count-change', cnt),
  { immediate: true }
)

function initSortable() {
  if (sortableInstance) {
    sortableInstance.destroy()
    sortableInstance = null
  }
  if (!tbodyRef.value) return
  sortableInstance = Sortable.create(tbodyRef.value, {
    handle: '.drag-handle',
    animation: 140,
    onEnd: (evt) => {
      if (evt.oldIndex !== undefined && evt.newIndex !== undefined && evt.oldIndex !== evt.newIndex) {
        moveStore(evt.oldIndex, evt.newIndex)
      }
    }
  })
}

async function loadStores() {
  loading.value = true
  try {
    const data = await goldSourcesApi.listAdmin()
    stores.value = Array.isArray(data) ? data : []
    if (stores.value.length > 0 && stores.value[0].interval_minutes) {
      bulkInterval.value = stores.value[0].interval_minutes
    }
    await nextTick()
    initSortable()
  } catch (err) {
    emit('toast', err.response?.data?.detail || 'Không thể tải danh sách cửa hàng.', 'error')
  } finally {
    loading.value = false
  }
}

async function handleApplyBulkInterval() {
  const minutes = Number(bulkInterval.value)
  if (!Number.isInteger(minutes) || minutes < 1 || minutes > 1440) {
    emit('toast', 'Chu kỳ quét phải từ 1 đến 1440 phút.', 'error')
    return
  }

  applyingBulk.value = true
  try {
    const updatedList = await goldSourcesApi.setIntervalAll(minutes)
    if (Array.isArray(updatedList)) {
      stores.value = updatedList
    } else {
      stores.value = stores.value.map((s) => ({ ...s, interval_minutes: minutes }))
    }
    emit('interval-all-changed', minutes)
    emit('toast', `Đã đặt chu kỳ ${minutes} phút cho tất cả ${stores.value.length} cửa hàng.`, 'success')
  } catch (err) {
    emit('toast', err.response?.data?.detail || 'Không thể áp dụng chu kỳ cho các cửa hàng.', 'error')
  } finally {
    applyingBulk.value = false
  }
}

async function moveStore(oldIndex, newIndex) {
  if (
    oldIndex < 0 ||
    newIndex < 0 ||
    oldIndex >= stores.value.length ||
    newIndex >= stores.value.length ||
    oldIndex === newIndex
  ) {
    return
  }

  const snapshot = [...stores.value]
  const updated = [...stores.value]
  const [moved] = updated.splice(oldIndex, 1)
  updated.splice(newIndex, 0, moved)
  stores.value = updated

  try {
    const ids = updated.map((s) => s.id)
    const serverList = await goldSourcesApi.reorder(ids)
    if (Array.isArray(serverList)) {
      stores.value = serverList
    }
    emit('toast', 'Đã cập nhật thứ tự hiển thị cửa hàng.', 'success')
  } catch (err) {
    stores.value = snapshot
    emit('toast', err.response?.data?.detail || 'Không thể lưu thứ tự cửa hàng.', 'error')
  }
}

function onNativeDragStart(idx, event) {
  draggedIdx = idx
  if (event?.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
  }
}

async function onNativeDrop(targetIdx) {
  if (draggedIdx === null || draggedIdx === targetIdx) return
  const from = draggedIdx
  draggedIdx = null
  await moveStore(from, targetIdx)
}

function resetForm() {
  form.name = ''
  form.url = ''
  form.interval_minutes = 10
  form.is_enabled = true
  form.extract_rules.mode = 'AUTO'
  form.extract_rules.price_url = ''
  form.extract_rules.row_selector = ''
  form.extract_rules.name_selector = ''
  form.extract_rules.buy_selector = ''
  form.extract_rules.sell_selector = ''
  form.extract_rules.column_order = 'BUY_SELL'
  formModal.error = ''
  formModal.showAdvanced = false
  draftTestResult.value = null
}

function openCreateModal() {
  resetForm()
  formModal.isEdit = false
  formModal.editId = null
  formModal.open = true
}

function openEditModal(store) {
  resetForm()
  formModal.isEdit = true
  formModal.editId = store.id
  form.name = store.name
  form.url = store.url
  form.interval_minutes = store.interval_minutes || 10
  form.is_enabled = Boolean(store.is_enabled)

  if (store.extract_rules) {
    form.extract_rules.mode = store.extract_rules.mode || 'AUTO'
    form.extract_rules.price_url = store.extract_rules.price_url || ''
    form.extract_rules.row_selector = store.extract_rules.row_selector || ''
    form.extract_rules.name_selector = store.extract_rules.name_selector || ''
    form.extract_rules.buy_selector = store.extract_rules.buy_selector || ''
    form.extract_rules.sell_selector = store.extract_rules.sell_selector || ''
    form.extract_rules.column_order = store.extract_rules.column_order || 'BUY_SELL'
    if (form.extract_rules.mode === 'CSS' || form.extract_rules.price_url) {
      formModal.showAdvanced = true
    }
  }
  formModal.open = true
}

function closeFormModal() {
  formModal.open = false
}

function buildExtractRulesPayload() {
  const r = form.extract_rules
  const hasAny =
    r.mode === 'CSS' ||
    (r.price_url && r.price_url.trim()) ||
    (r.row_selector && r.row_selector.trim())
  if (!hasAny) return null
  return {
    mode: r.mode || 'AUTO',
    price_url: r.price_url?.trim() || null,
    row_selector: r.row_selector?.trim() || null,
    name_selector: r.name_selector?.trim() || null,
    buy_selector: r.buy_selector?.trim() || null,
    sell_selector: r.sell_selector?.trim() || null,
    column_order: r.column_order || 'BUY_SELL'
  }
}

async function handleTestDraft() {
  if (!form.url.trim()) return
  testingDraft.value = true
  draftTestResult.value = null
  formModal.error = ''
  try {
    const res = await goldSourcesApi.testDraft({
      url: form.url.trim(),
      extract_rules: buildExtractRulesPayload()
    })
    draftTestResult.value = res
  } catch (err) {
    formModal.error = err.response?.data?.detail || 'Quét thử không thành công.'
  } finally {
    testingDraft.value = false
  }
}

async function handleSubmitForm() {
  formModal.error = ''
  if (!form.name.trim() || !form.url.trim()) {
    formModal.error = 'Vui lòng nhập đầy đủ tên cửa hàng và link trang web.'
    return
  }

  savingForm.value = true
  const payload = {
    name: form.name.trim(),
    url: form.url.trim(),
    interval_minutes: Number(form.interval_minutes) || 10,
    is_enabled: Boolean(form.is_enabled),
    extract_rules: buildExtractRulesPayload()
  }

  try {
    if (formModal.isEdit && formModal.editId) {
      const updated = await goldSourcesApi.update(formModal.editId, payload)
      const idx = stores.value.findIndex((s) => s.id === formModal.editId)
      if (idx !== -1) stores.value[idx] = updated
      emit('toast', `Đã cập nhật cửa hàng "${updated.name}".`, 'success')
    } else {
      const created = await goldSourcesApi.create(payload)
      stores.value.push(created)
      await nextTick()
      initSortable()
      emit('toast', `Đã thêm cửa hàng "${created.name}".`, 'success')
    }
    formModal.open = false
  } catch (err) {
    formModal.error = err.response?.data?.detail || 'Không thể lưu thông tin cửa hàng.'
  } finally {
    savingForm.value = false
  }
}

async function handleToggleEnabled(store, checked) {
  const prev = store.is_enabled
  store.is_enabled = checked
  try {
    const updated = await goldSourcesApi.update(store.id, { is_enabled: checked })
    const idx = stores.value.findIndex((s) => s.id === store.id)
    if (idx !== -1) stores.value[idx] = updated
    emit('toast', `${checked ? 'Đã bật' : 'Đã tắt'} tự động quét cho "${store.name}".`, 'success')
  } catch (err) {
    store.is_enabled = prev
    emit('toast', err.response?.data?.detail || 'Không thể đổi trạng thái cửa hàng.', 'error')
  }
}

async function handleTestSaved(store) {
  testingId.value = store.id
  try {
    const res = await goldSourcesApi.testSaved(store.id)
    // Cập nhật ngay trạng thái quét trên dòng của bảng
    store.last_status = res.status
    store.last_message = res.message
    store.last_row_count = res.row_count
    store.last_duration_ms = res.duration_ms
    store.last_strategy = res.strategy
    store.last_scan_at = new Date().toISOString()

    testModal.storeName = store.name
    testModal.result = res
    testModal.open = true
  } catch (err) {
    store.last_status = 'ERROR'
    store.last_message = err.response?.data?.detail || 'Lỗi kết nối khi quét thử.'
    emit('toast', store.last_message, 'error')
  } finally {
    testingId.value = null
  }
}

async function openDeleteModal(store) {
  deleteModal.store = store
  deleteModal.historyCount = 0
  deleteModal.deleting = false
  deleteModal.open = true
  try {
    const preview = await goldSourcesApi.remove(store.id, true)
    deleteModal.historyCount = preview.history_count || 0
  } catch {
    deleteModal.historyCount = 0
  }
}

async function confirmDeleteStore() {
  if (!deleteModal.store) return
  deleteModal.deleting = true
  try {
    const res = await goldSourcesApi.remove(deleteModal.store.id, false)
    stores.value = stores.value.filter((s) => s.id !== deleteModal.store.id)
    deleteModal.open = false
    emit('toast', res.message || `Đã xóa cửa hàng "${deleteModal.store.name}".`, 'success')
  } catch (err) {
    emit('toast', err.response?.data?.detail || 'Không thể xóa cửa hàng.', 'error')
  } finally {
    deleteModal.deleting = false
  }
}

function formatShortUrl(url) {
  if (!url) return ''
  return url.replace(/^https?:\/\//i, '').replace(/\/$/, '')
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())} ${pad(d.getDate())}/${pad(d.getMonth() + 1)}`
}

function formatVnd(val) {
  if (val === null || val === undefined || isNaN(val)) return '–'
  return Math.round(Number(val)).toLocaleString('vi-VN') + ' đ'
}

function buildStatusTooltip(store) {
  const parts = []
  if (store.last_status === 'SUCCESS') parts.push('Trạng thái: Thành công')
  else if (store.last_status === 'ERROR') parts.push('Trạng thái: Thất bại')
  else parts.push('Trạng thái: Chưa quét')
  if (store.last_message) parts.push(store.last_message)
  if (store.last_strategy) parts.push(`Chiến lược: ${store.last_strategy}`)
  if (store.last_duration_ms) parts.push(`Thời lượng: ${store.last_duration_ms}ms`)
  return parts.join(' | ')
}

onMounted(() => {
  loadStores()
})

onBeforeUnmount(() => {
  if (sortableInstance) {
    sortableInstance.destroy()
    sortableInstance = null
  }
})

defineExpose({
  stores,
  loadStores,
  moveStore,
  handleApplyBulkInterval
})
</script>

<style scoped>
.store-manager {
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

.store-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.15rem 1.35rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-top: 3px solid var(--accent);
  border-radius: var(--radius-md);
}

.toolbar-info h3 {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-main);
  margin-bottom: 0.25rem;
}

.toolbar-info p {
  font-size: 0.8125rem;
  color: var(--text-muted);
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.store-table-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.store-empty-state {
  padding: 3rem 1.5rem;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.875rem;
}

.empty-store-icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-muted);
}

.store-table-scroll {
  overflow-x: auto;
}

.store-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.store-table thead th {
  background-color: var(--bg-sidebar);
  padding: 0.75rem 1rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}

.store-table tbody tr {
  border-bottom: 1px solid var(--border);
  transition: background-color 0.12s ease;
}

.store-table tbody tr:hover {
  background-color: var(--bg-hover);
}

.store-table tbody td {
  padding: 0.75rem 1rem;
  font-size: 0.84rem;
  vertical-align: middle;
}

.col-drag {
  width: 42px;
  text-align: center;
  padding-right: 0.25rem !important;
}

.col-order {
  width: 110px;
}

.drag-handle {
  background: none;
  border: 1px solid transparent;
  color: var(--text-muted);
  cursor: grab;
  padding: 0.25rem 0.35rem;
  border-radius: var(--radius-sm);
  font-size: 1rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.drag-handle:hover {
  background-color: var(--bg-sidebar);
  border-color: var(--border);
  color: var(--text-main);
}

.order-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-weight: 600;
  font-size: 0.78rem;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.order-pill.is-default {
  color: var(--highlight);
}

.default-tag {
  background-color: var(--highlight-soft);
  color: var(--highlight);
  border: 1px solid var(--border);
  padding: 0.1rem 0.4rem;
  border-radius: var(--radius-sm);
  font-size: 0.6875rem;
  font-weight: 600;
}

.store-name-cell {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.store-name-text {
  font-weight: 600;
  color: var(--text-main);
}

.rule-tag {
  font-size: 0.6875rem;
  font-weight: 600;
  padding: 0.05rem 0.35rem;
  border-radius: var(--radius-sm);
  background-color: var(--accent-soft);
  color: var(--accent);
  border: 1px solid var(--border);
}

.store-url-link {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  color: var(--accent);
  text-decoration: none;
  font-size: 0.8125rem;
  max-width: 240px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.store-url-link:hover {
  text-decoration: underline;
}

.interval-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.2rem 0.55rem;
  border-radius: var(--radius-sm);
  background-color: var(--bg-sidebar);
  border: 1px solid var(--border);
  color: var(--text-main);
  font-size: 0.78rem;
  font-variant-numeric: tabular-nums;
}

.scan-status-cell {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  max-width: 240px;
}

.scan-status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  width: fit-content;
  padding: 0.175rem 0.55rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
}

.scan-status-badge.status-success {
  background-color: var(--accent-soft);
  color: var(--accent);
  border: 1px solid var(--border);
}

.scan-status-badge.status-error {
  background-color: var(--danger-soft);
  color: var(--danger);
  border: 1px solid var(--danger);
}

.scan-status-badge.status-never {
  background-color: var(--bg-sidebar);
  color: var(--text-muted);
  border: 1px solid var(--border);
}

.scan-status-sub {
  font-size: 0.72rem;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.scan-status-time {
  font-size: 0.6875rem;
  color: var(--text-muted);
  font-variant-numeric: tabular-nums;
}

.text-right {
  text-align: right;
}

.row-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
}

.btn-row-action {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.325rem 0.65rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background-color: var(--bg-sidebar);
  color: var(--text-main);
  font-family: var(--font-ui);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.12s ease, border-color 0.12s ease, color 0.12s ease;
  white-space: nowrap;
}

.btn-row-action.btn-test {
  border-color: var(--accent);
  color: var(--accent);
}

.btn-row-action.btn-test:hover:not(:disabled) {
  background-color: var(--accent-soft);
}

.btn-row-action.btn-edit:hover:not(:disabled) {
  background-color: var(--bg-hover);
}

.btn-row-action.btn-del {
  color: var(--danger);
}

.btn-row-action.btn-del:hover:not(:disabled) {
  background-color: var(--danger-soft);
  border-color: var(--danger);
}

.btn-row-action:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

/* Toggle Switch */
.switch {
  position: relative;
  display: inline-block;
  width: 40px;
  height: 22px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background-color: var(--border);
  transition: 0.15s;
  border-radius: 22px;
}

.slider::before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 3px;
  bottom: 3px;
  background-color: var(--text-main);
  transition: 0.15s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: var(--accent);
}

input:checked + .slider::before {
  transform: translateX(18px);
  background-color: var(--on-accent);
}

/* Modals */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background-color: rgba(2, 6, 16, 0.72);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1200;
  padding: 1rem;
}

.modal-card {
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-pop);
  overflow: hidden;
}

.modal-card.modal-wide {
  max-width: 640px;
}

.modal-header {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-main);
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.95rem;
  padding: 0.25rem;
}

.modal-body {
  padding: 1.25rem;
  overflow-y: auto;
  font-size: 0.875rem;
  color: var(--text-main);
}

.form-stack {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-row-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.form-group label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--text-main);
}

.interval-input-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.preset-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.preset-chip {
  padding: 0.2rem 0.5rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background-color: var(--bg-sidebar);
  color: var(--text-muted);
  font-family: var(--font-ui);
  font-size: 0.75rem;
  cursor: pointer;
}

.preset-chip.active {
  background-color: var(--accent-soft);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
}

.checkbox-inline {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  margin-top: 0.35rem;
  font-size: 0.8125rem;
}

.checkbox-inline input {
  width: 16px;
  height: 16px;
  accent-color: var(--accent);
}

.advanced-box {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background-color: var(--bg-sidebar);
  overflow: hidden;
}

.advanced-toggle-btn {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.65rem 0.875rem;
  background: none;
  border: none;
  color: var(--text-main);
  font-family: var(--font-ui);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
}

.advanced-body {
  padding: 0.875rem;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.mode-radios {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.radio-label {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.8125rem;
  cursor: pointer;
}

.css-rules-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.form-error-alert {
  padding: 0.65rem 0.85rem;
  border-radius: var(--radius-sm);
  background-color: var(--danger-soft);
  border: 1px solid var(--danger);
  color: var(--danger);
  font-size: 0.8125rem;
}

.test-result-box,
.test-summary-banner {
  padding: 0.75rem 0.9rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
}

.box-ok,
.banner-ok {
  background-color: var(--accent-soft);
  border-color: var(--accent);
}

.box-err,
.banner-err {
  background-color: var(--danger-soft);
  border-color: var(--danger);
  color: var(--danger);
}

.test-result-header,
.banner-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.5rem;
  font-size: 0.84rem;
}

.test-result-title {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 600;
}

.test-meta-tag,
.banner-sub {
  display: flex;
  gap: 0.85rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.preview-table-wrap {
  margin-top: 0.75rem;
  overflow-x: auto;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8125rem;
  font-variant-numeric: tabular-nums;
}

.preview-table th,
.preview-table td {
  padding: 0.45rem 0.65rem;
  border: 1px solid var(--border);
  text-align: left;
}

.preview-table th {
  background-color: var(--bg-sidebar);
  color: var(--text-muted);
  font-weight: 600;
}

.text-buy {
  color: var(--accent);
  font-weight: 600;
}

.text-sell {
  color: var(--highlight);
  font-weight: 600;
}

.preview-note {
  margin-top: 0.55rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.delete-warning-box {
  margin-top: 0.875rem;
  padding: 0.75rem;
  border-radius: var(--radius-sm);
  background-color: var(--danger-soft);
  border: 1px solid var(--danger);
  color: var(--danger);
  font-size: 0.8125rem;
}

.modal-footer {
  padding: 0.875rem 1.25rem;
  background-color: var(--bg-sidebar);
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.footer-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: auto;
}

.btn-danger {
  background-color: var(--danger);
  color: var(--on-danger);
  border: 1px solid var(--danger);
}

.text-danger {
  color: var(--danger);
}

.spinner-inline {
  width: 13px;
  height: 13px;
  border: 2px solid var(--border);
  border-top-color: currentColor;
  border-radius: 50%;
  display: inline-block;
  animation: spin 0.75s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .form-row-2,
  .css-rules-grid {
    grid-template-columns: 1fr;
  }
}

.bulk-interval-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 0.7rem 1rem;
  background-color: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
}

.bulk-interval-label {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-main);
}

.bulk-interval-label i {
  color: var(--accent);
}

.bulk-interval-controls {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.bulk-preset-pills {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

.bulk-pill-btn {
  padding: 0.28rem 0.6rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background-color: var(--bg-sidebar);
  color: var(--text-muted);
  font-family: var(--font-ui);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
}

.bulk-pill-btn:hover {
  border-color: var(--accent);
  color: var(--text-main);
}

.bulk-pill-btn.active {
  background-color: var(--accent);
  border-color: var(--accent);
  color: var(--on-accent);
}

.bulk-input-group {
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background-color: var(--bg-sidebar);
  overflow: hidden;
}

.bulk-number-input {
  width: 58px;
  padding: 0.28rem 0.45rem;
  border: none;
  background: transparent;
  color: var(--text-main);
  font-family: var(--font-ui);
  font-size: 0.78rem;
  font-weight: 600;
  text-align: center;
}

.bulk-number-input:focus {
  outline: none;
}

.bulk-unit {
  padding: 0 0.45rem 0 0.15rem;
  font-size: 0.72rem;
  color: var(--text-muted);
}

.btn-apply-bulk {
  padding: 0.32rem 0.75rem;
  font-size: 0.78rem;
  border-color: var(--accent);
  color: var(--accent);
}

.btn-apply-bulk:hover:not(:disabled) {
  background-color: var(--accent);
  color: var(--on-accent);
}
</style>

