<template>
  <div class="app-container">
    <!-- Navbar -->
    <header class="navbar">
      <div class="navbar-inner">
        <div class="brand">
          <div class="brand-icon">
            <QrCode :size="24" />
          </div>
          <div class="brand-text">
            <h1>QR kód stopovačka</h1>
          </div>
        </div>

        <div class="nav-actions">
          <div
            class="status-pill"
            :class="health.status === 'healthy' ? 'healthy' : 'degraded'"
            :title="`DB: ${health.database}`"
          >
            <span class="status-dot pulse"></span>
            <span>{{ health.status === 'healthy' ? 'Systém online' : 'Připojování...' }}</span>
          </div>

          <button class="btn btn-primary" @click="openCreateModal">
            <Plus :size="18" />
            <span>Nový QR kód</span>
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Toolbar & Stats -->
      <div class="top-bar">
        <div class="search-wrapper">
          <Search :size="18" class="search-icon-pos" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Hledat podle textu, popisu nebo čísla..."
            class="search-input"
          />
        </div>

        <div class="stats-card-group">
          <div class="stat-item">
            <div class="stat-icon">
              <QrCode :size="18" />
            </div>
            <div class="stat-content">
              <span class="stat-label">Celkem kódů</span>
              <span class="stat-val">{{ filteredQrList.length }}</span>
            </div>
          </div>

          <button
            class="btn btn-secondary btn-icon-only"
            title="Obnovit seznam"
            :disabled="isLoading"
            @click="fetchQrCodes"
          >
            <RefreshCw :size="18" :class="{ spinner: isLoading }" />
          </button>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading && qrList.length === 0" class="empty-state">
        <div class="spinner spinner-dark" style="width: 32px; height: 32px; margin: 0 auto 1rem;"></div>
        <h3>Načítání QR kódů...</h3>
        <p>Probíhá stahování dat z relační databáze.</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="filteredQrList.length === 0" class="empty-state">
        <div class="empty-icon">
          <QrCode :size="32" />
        </div>
        <h3 v-if="searchQuery">Žádné výsledky vyhledávání</h3>
        <h3 v-else>Zatím žádné QR kódy</h3>
        <p v-if="searchQuery">
          Pro zadaný výraz "{{ searchQuery }}" nebyl nalezen žádný záznam.
        </p>
        <p v-else>
          Vytvořte svůj první QR kód. Bude vygenerován a automaticky uložen do relační databáze.
        </p>
        <button class="btn btn-primary" @click="openCreateModal">
          <Plus :size="18" />
          <span>Vytvořit první QR kód</span>
        </button>
      </div>

      <!-- Grid of QR Codes -->
      <div v-else class="qr-grid">
        <div v-for="item in filteredQrList" :key="item.id" class="qr-card">
          <!-- Card Header -->
          <div class="qr-card-header">
            <span class="qr-badge-code">{{ item.code_number || `QR-${item.id}` }}</span>
            <span class="qr-date">{{ formatDate(item.created_at) }}</span>
          </div>

          <!-- Card QR Preview Thumbnail -->
          <div class="qr-card-preview" @click="openDetail(item)" title="Klikněte pro zvětšení náhledu">
            <img :src="item.image_url" :alt="item.description || item.code_number" loading="lazy" />
            <div class="qr-hover-overlay">
              <Eye :size="20" style="margin-right: 6px;" />
              <span>Detail</span>
            </div>
          </div>

          <!-- Card Body -->
          <div class="qr-card-body">
            <h4 class="qr-title">{{ item.description || 'Bez popisu' }}</h4>

            <!-- QR Content Box -->
            <div class="qr-text-box">
              <span class="qr-text-content" :title="item.content">{{ item.content }}</span>
              <button
                class="btn btn-secondary btn-sm btn-icon-only"
                title="Kopírovat text"
                @click.stop="copyToClipboard(item.content)"
              >
                <Check v-if="copiedText === item.content" :size="14" style="color: var(--success);" />
                <Copy v-else :size="14" />
              </button>
            </div>
          </div>

          <!-- Card Footer -->
          <div class="qr-card-footer">
            <div class="storage-pill" title="Uloženo v PostgreSQL databázi (včetně binárních dat)">
              <Database :size="13" />
              <span>PostgreSQL</span>
            </div>

            <div style="display: flex; gap: 0.4rem;">
              <a
                :href="`${item.image_url}?download=1`"
                class="btn btn-secondary btn-sm"
                title="Stáhnout PNG"
              >
                <Download :size="15" />
              </a>
              <button
                class="btn btn-danger btn-sm"
                title="Smazat QR kód"
                @click="confirmDelete(item)"
              >
                <Trash2 :size="15" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Modal: Vytvořit nový QR kód -->
    <div v-if="showCreateModal" class="modal-backdrop" @click.self="showCreateModal = false">
      <div class="modal-dialog">
        <div class="modal-header">
          <h3 class="modal-title">Nový QR kód</h3>
          <button class="btn btn-secondary btn-icon-only btn-sm" @click="showCreateModal = false">
            <X :size="18" />
          </button>
        </div>

        <form @submit.prevent="saveQrCode">
          <div class="modal-body">
            <!-- Text / Obsah -->
            <div class="form-group">
              <label class="form-label">
                <span>Obsah QR kódu (URL / Text) *</span>
                <span class="form-hint">{{ form.content.length }} znaků</span>
              </label>
              <textarea
                v-model="form.content"
                class="form-textarea"
                rows="3"
                placeholder="Např. https://moje-aplikace.cz nebo libovolný text pro QR kód..."
                required
                @input="handleContentChange"
              ></textarea>
            </div>

            <!-- Popis -->
            <div class="form-group">
              <label class="form-label">Popis / Název</label>
              <input
                v-model="form.description"
                type="text"
                class="form-input"
                placeholder="Např. Odkaz na registraci uživatele"
              />
            </div>

            <!-- Číslo QR kódu -->
            <div class="form-group">
              <label class="form-label">Číslo / Identifikátor</label>
              <input
                v-model="form.code_number"
                type="text"
                class="form-input"
                placeholder="Např. QR-2024-001 (nechte prázdné pro automatické číslo)"
              />
              <span class="form-hint">Pokud nezadáte, bude číslo vygenerováno automaticky systémem.</span>
            </div>

            <!-- Živý náhled -->
            <div class="form-group">
              <label class="form-label">Živý náhled generování</label>
              <div class="live-preview-box">
                <div v-if="previewLoading" class="spinner spinner-dark"></div>
                <img
                  v-else-if="previewImage"
                  :src="previewImage"
                  alt="Náhled QR kódu"
                  class="live-preview-img"
                />
                <div v-else style="color: var(--text-muted); font-size: 0.85rem; text-align: center;">
                  Zadejte obsah pro vygenerování náhledu QR kódu
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary"
              :disabled="isSubmitting"
              @click="showCreateModal = false"
            >
              Zrušit
            </button>
            <button
              type="submit"
              class="btn btn-primary"
              :disabled="isSubmitting || !form.content.trim()"
            >
              <span v-if="isSubmitting" class="spinner"></span>
              <Database v-else :size="16" />
              <span>{{ isSubmitting ? 'Ukládám do DB...' : 'Uložit do databáze' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal: Detail QR kódu -->
    <div v-if="showDetailModal && selectedQr" class="modal-backdrop" @click.self="showDetailModal = false">
      <div class="modal-dialog">
        <div class="modal-header">
          <h3 class="modal-title">Detail QR kódu ({{ selectedQr.code_number }})</h3>
          <button class="btn btn-secondary btn-icon-only btn-sm" @click="showDetailModal = false">
            <X :size="18" />
          </button>
        </div>

        <div class="modal-body" style="align-items: center; text-align: center;">
          <img
            :src="selectedQr.image_url"
            :alt="selectedQr.description"
            style="width: 220px; height: 220px; border: 1px solid var(--border); border-radius: var(--radius-md); padding: 8px; background: white;"
          />

          <div style="width: 100%; text-align: left; margin-top: 1rem; display: flex; flex-direction: column; gap: 0.75rem;">
            <div>
              <span class="stat-label">Popis:</span>
              <div style="font-weight: 600;">{{ selectedQr.description || 'Bez popisu' }}</div>
            </div>

            <div>
              <span class="stat-label">Obsah textu:</span>
              <div class="qr-text-box" style="margin-top: 0.25rem;">
                <span class="qr-text-content">{{ selectedQr.content }}</span>
                <button
                  class="btn btn-secondary btn-sm btn-icon-only"
                  @click="copyToClipboard(selectedQr.content)"
                >
                  <Copy :size="14" />
                </button>
              </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
              <div>
                <span class="stat-label">Úložiště:</span>
                <div style="font-family: var(--font-mono); font-size: 0.75rem;">
                  PostgreSQL (BYTEA)
                </div>
              </div>
              <div>
                <span class="stat-label">Formát:</span>
                <div style="font-family: var(--font-mono); font-size: 0.75rem;">
                  image/png
                </div>
              </div>
            </div>

            <div>
              <span class="stat-label">Vytvořeno:</span>
              <div style="font-size: 0.85rem;">{{ formatDate(selectedQr.created_at) }}</div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <a
            :href="`${selectedQr.image_url}?download=1`"
            class="btn btn-primary"
          >
            <Download :size="16" />
            <span>Stáhnout PNG</span>
          </a>
          <button class="btn btn-secondary" @click="showDetailModal = false">
            Zavřít
          </button>
        </div>
      </div>
    </div>

    <!-- Toast Notifications -->
    <div class="toast-container">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="toast"
        :class="toast.type"
      >
        <span>{{ toast.message }}</span>
      </div>
    </div>

    <!-- Footer -->
    <footer class="app-footer">
      <p>Semestrální práce DCE (odevzdání v1)</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue';
import {
  QrCode,
  Plus,
  Search,
  RefreshCw,
  Copy,
  Check,
  Download,
  Trash2,
  X,
  Eye,
  Database,
} from 'lucide-vue-next';

// ============================================================================
// Reactive State Management
// ============================================================================
const qrList = ref([]);              // List of loaded QR codes from database
const searchQuery = ref('');         // Active search query term
const isLoading = ref(false);        // Loading state indicator for list
const isSubmitting = ref(false);     // Form submission in-progress flag
const showCreateModal = ref(false);  // Visibility of creation modal dialog
const showDetailModal = ref(false);  // Visibility of detail modal dialog
const selectedQr = ref(null);        // Currently selected QR code for detail modal
const copiedText = ref(null);        // Recently copied text payload (for icon state)

// System and database connectivity status (fetched from /api/health)
const health = ref({
  status: 'checking',
  database: 'checking',
});

// New QR code form state
const form = reactive({
  content: '',
  description: '',
  code_number: '',
});

// Live generation preview state
const previewImage = ref('');
const previewLoading = ref(false);
let previewDebounceTimer = null;

// Notification toast system
const toasts = ref([]);

// ============================================================================
// Computed Properties
// ============================================================================
// Client-side search filtering across code number, description, and content
const filteredQrList = computed(() => {
  if (!searchQuery.value.trim()) return qrList.value;
  const q = searchQuery.value.toLowerCase().trim();
  return qrList.value.filter(item => {
    return (
      (item.code_number && item.code_number.toLowerCase().includes(q)) ||
      (item.description && item.description.toLowerCase().includes(q)) ||
      (item.content && item.content.toLowerCase().includes(q))
    );
  });
});

// ============================================================================
// Helper Utilities
// ============================================================================
// Display transient toast alert notification (info, success, error)
const showToast = (message, type = 'info', duration = 3500) => {
  const id = Date.now() + Math.random();
  toasts.value.push({ id, message, type });
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id);
  }, duration);
};

// ============================================================================
// Backend API Interactions
// ============================================================================
// Query healthcheck endpoint (/api/health)
const checkHealth = async () => {
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    health.value = data;
  } catch (err) {
    health.value = {
      status: 'degraded',
      database: 'chyba',
    };
  }
};

// Fetch all QR code records from database
const fetchQrCodes = async () => {
  isLoading.value = true;
  try {
    const res = await fetch('/api/qrcodes');
    if (!res.ok) throw new Error('Chyba při stahování QR kódů');
    const data = await res.json();
    qrList.value = data;
  } catch (err) {
    showToast(`Nepodařilo se načíst QR kódy: ${err.message}`, 'error');
  } finally {
    isLoading.value = false;
  }
};

// Debounced live QR preview generator (300 ms delay)
const handleContentChange = () => {
  if (previewDebounceTimer) clearTimeout(previewDebounceTimer);
  const text = form.content.trim();
  if (!text) {
    previewImage.value = '';
    return;
  }
  previewDebounceTimer = setTimeout(async () => {
    previewLoading.value = true;
    try {
      const res = await fetch('/api/qrcodes/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text }),
      });
      if (res.ok) {
        const data = await res.json();
        previewImage.value = data.preview;
      }
    } catch (err) {
      console.warn('Preview error:', err);
    } finally {
      previewLoading.value = false;
    }
  }, 300);
};

// Open creation modal and reset form inputs
const openCreateModal = () => {
  form.content = '';
  form.description = '';
  form.code_number = '';
  previewImage.value = '';
  showCreateModal.value = true;
};

// Submit and persist new QR code into database (POST /api/qrcodes)
const saveQrCode = async () => {
  if (!form.content.trim()) {
    showToast('Zadejte prosím text pro QR kód.', 'error');
    return;
  }

  isSubmitting.value = true;
  try {
    const res = await fetch('/api/qrcodes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: form.content.trim(),
        description: form.description.trim(),
        code_number: form.code_number.trim(),
      }),
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.error || 'Uložení selhalo.');
    }

    const created = await res.json();
    // Prepend newly created item to the top of the list
    qrList.value.unshift(created);
    showCreateModal.value = false;
    showToast(`QR kód ${created.code_number} byl úspěšně uložen do databáze!`, 'success');
  } catch (err) {
    showToast(`Chyba: ${err.message}`, 'error');
  } finally {
    isSubmitting.value = false;
  }
};

// Open detailed view modal for a QR code
const openDetail = (item) => {
  selectedQr.value = item;
  showDetailModal.value = true;
};

// Delete QR code from database after user confirmation (DELETE /api/qrcodes/:id)
const confirmDelete = async (item) => {
  if (!confirm(`Opravdu chcete smazat QR kód "${item.code_number || item.id}" z databáze?`)) {
    return;
  }

  try {
    const res = await fetch(`/api/qrcodes/${item.id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Nepodařilo se smazat QR kód');

    qrList.value = qrList.value.filter(q => q.id !== item.id);
    showToast(`QR kód ${item.code_number} byl smazán.`, 'success');
  } catch (err) {
    showToast(`Chyba: ${err.message}`, 'error');
  }
};

// Copy text payload to clipboard with feedback animation
const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    copiedText.value = text;
    showToast('Text QR kódu byl zkopírován do schránky.', 'info', 2000);
    setTimeout(() => {
      if (copiedText.value === text) copiedText.value = null;
    }, 2500);
  } catch (err) {
    showToast('Nepodařilo se zkopírovat text do schránky.', 'error');
  }
};

// Format ISO timestamp to localized Czech date-time string
const formatDate = (isoStr) => {
  if (!isoStr) return '';
  const date = new Date(isoStr);
  return date.toLocaleString('cs-CZ', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// ============================================================================
// Component Lifecycle Hooks
// ============================================================================
onMounted(() => {
  // Initial healthcheck and data retrieval
  checkHealth();
  fetchQrCodes();
  // Periodic system healthcheck polling every 30 seconds
  setInterval(checkHealth, 30000);
});
</script>
