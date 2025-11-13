<template>
  <main class="container">
    <header>
      <h1>Gemini File Search Demo</h1>
      <p class="subtitle">
        Quản lý sản phẩm điện tử, đồng bộ embedding với Gemini và OpenSearch.
      </p>
    </header>

    <section class="panel">
      <h2>Thêm / cập nhật sản phẩm</h2>
      <form @submit.prevent="submitProduct">
        <label>
          Tên sản phẩm
          <input v-model="productForm.name" type="text" required />
        </label>
        <label>
          Mô tả
          <textarea v-model="productForm.description" rows="4"></textarea>
        </label>
        <label>
          Ảnh (URL, phân tách bởi dấu phẩy)
          <input
            v-model="productForm.images"
            type="text"
            placeholder="https://example.com/img1.jpg, https://example.com/img2.jpg"
          />
        </label>
        <button type="submit" :disabled="saving">
          {{ saving ? "Đang lưu..." : productForm.id ? "Cập nhật" : "Thêm mới" }}
        </button>
        <button
          v-if="productForm.id"
          type="button"
          class="muted"
          @click="resetForm"
        >
          Huỷ
        </button>
      </form>
    </section>

    <section class="panel">
      <h2>Danh sách sản phẩm</h2>
      <div v-if="products.length === 0" class="empty">
        Chưa có sản phẩm nào. Hãy thêm mới!
      </div>
      <table v-else>
        <thead>
          <tr>
            <th>Tên</th>
            <th>Mô tả</th>
            <th>Ảnh</th>
            <th>Hành động</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="product in products" :key="product.id">
            <td>{{ product.name }}</td>
            <td class="description">{{ product.description }}</td>
            <td>
              <ul>
                <li v-for="img in product.images || []" :key="img">
                  <a :href="img" target="_blank" rel="noopener">{{ img }}</a>
                </li>
              </ul>
            </td>
            <td class="actions">
              <button @click="editProduct(product)">Sửa</button>
              <button class="danger" @click="deleteProduct(product.id)">
                Xoá
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="panel">
      <h2>Tìm kiếm (OpenSearch + Gemini)</h2>
      <form class="search-form" @submit.prevent="performSearch">
        <input
          v-model="query"
          type="text"
          placeholder="Nhập từ khoá..."
          required
        />
        <button type="submit" :disabled="searching">
          {{ searching ? "Đang tìm..." : "Tìm kiếm" }}
        </button>
      </form>
      <div v-if="searchResults.length === 0" class="empty">
        Không có kết quả.
      </div>
      <ul v-else class="results">
        <li v-for="hit in searchResults" :key="hit.chunk_id">
          <h3>{{ hit.name }}</h3>
          <p>{{ hit.chunk_text }}</p>
          <small>Score: {{ hit.score.toFixed(3) }}</small>
        </li>
      </ul>
    </section>
  </main>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const products = ref([]);
const searchResults = ref([]);
const query = ref("");
const saving = ref(false);
const searching = ref(false);

const productForm = reactive({
  id: null,
  name: "",
  description: "",
  images: "",
});

function resetForm() {
  productForm.id = null;
  productForm.name = "";
  productForm.description = "";
  productForm.images = "";
}

async function loadProducts() {
  const response = await fetch(`${API_BASE}/products/`);
  products.value = await response.json();
}

function parseImages(value) {
  if (!value) return [];
  return value
    .split(",")
    .map((url) => url.trim())
    .filter(Boolean);
}

async function submitProduct() {
  saving.value = true;
  try {
    const payload = {
      name: productForm.name,
      description: productForm.description,
      images: parseImages(productForm.images),
    };

    let url = `${API_BASE}/products/`;
    let method = "POST";
    if (productForm.id) {
      url = `${API_BASE}/products/${productForm.id}`;
      method = "PUT";
    }

    const response = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error("Không thể lưu sản phẩm");
    }
    await loadProducts();
    resetForm();
  } finally {
    saving.value = false;
  }
}

function editProduct(product) {
  productForm.id = product.id;
  productForm.name = product.name;
  productForm.description = product.description || "";
  productForm.images = (product.images || []).join(", ");
}

async function deleteProduct(id) {
  if (!confirm("Bạn có chắc muốn xoá sản phẩm này?")) return;
  await fetch(`${API_BASE}/products/${id}`, { method: "DELETE" });
  await loadProducts();
}

async function performSearch() {
  searching.value = true;
  try {
    const response = await fetch(
      `${API_BASE}/search/?q=${encodeURIComponent(query.value)}`
    );
    const data = await response.json();
    searchResults.value = data.hits || [];
  } finally {
    searching.value = false;
  }
}

onMounted(() => {
  loadProducts();
});
</script>

<style scoped>
.container {
  max-width: 960px;
  margin: 0 auto;
  padding: 2rem;
  font-family: system-ui, sans-serif;
  color: #1f2933;
}

header {
  margin-bottom: 2rem;
}

.subtitle {
  color: #52606d;
  margin-top: 0.5rem;
}

.panel {
  background: #ffffff;
  border: 1px solid #e4e7eb;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 2px 4px rgba(15, 23, 42, 0.04);
}

form {
  display: grid;
  gap: 1rem;
}

label {
  display: grid;
  gap: 0.25rem;
  font-weight: 600;
}

input,
textarea,
button {
  font: inherit;
}

input,
textarea {
  border: 1px solid #d9e2ec;
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
}

button {
  background: #2563eb;
  color: #fff;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
}

button:disabled {
  background: #94a3b8;
  cursor: not-allowed;
}

button.muted {
  background: #e2e8f0;
  color: #1f2937;
}

button.danger {
  background: #dc2626;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  border-bottom: 1px solid #e2e8f0;
  text-align: left;
  padding: 0.75rem;
  vertical-align: top;
}

.description {
  max-width: 320px;
  white-space: pre-wrap;
}

.actions {
  display: flex;
  gap: 0.5rem;
}

.empty {
  color: #64748b;
}

.results {
  list-style: none;
  padding: 0;
  display: grid;
  gap: 1rem;
}

.results li {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
}

.search-form {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.search-form input {
  flex: 1;
}
</style>

