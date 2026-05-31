<template>
  <main class="novel-page">
    <div class="app-shell">
      <aside class="sidebar">
        <div class="side-top">
          <div class="brand" @click="goProject">AF</div>

          <el-tooltip content="项目" placement="right">
            <button class="nav-btn" aria-label="项目" @click="goProject">
              <el-icon><Folder /></el-icon>
            </button>
          </el-tooltip>

          <el-tooltip content="小说" placement="right">
            <button class="nav-btn active" aria-label="小说">
              <el-icon><Reading /></el-icon>
            </button>
          </el-tooltip>

          <el-tooltip content="任务" placement="right">
            <button class="nav-btn" aria-label="任务" @click="showComingSoon">
              <el-icon><List /></el-icon>
            </button>
          </el-tooltip>
        </div>

        <div class="side-bottom">
          <el-tooltip content="文档" placement="right">
            <button class="nav-btn" aria-label="文档" @click="showComingSoon">
              <el-icon><Document /></el-icon>
            </button>
          </el-tooltip>

          <el-tooltip content="设置" placement="right">
            <button class="nav-btn" aria-label="设置" @click="settingsVisible = true">
              <el-icon><Setting /></el-icon>
            </button>
          </el-tooltip>

          <el-tooltip content="代码仓库" placement="right">
            <button class="nav-btn" aria-label="代码仓库" @click="showComingSoon">
              <el-icon><Connection /></el-icon>
            </button>
          </el-tooltip>
        </div>
      </aside>

      <section class="main-panel">
        <header class="page-header">
          <div class="page-header__left">
            <h1 class="title">我的小说</h1>
            <p class="desc">管理章节、卷次结构与事件清洗结果</p>
          </div>

          <div class="page-header__right">
            <el-button class="header-action" size="large" @click="openImportDialog">
              <el-icon><Upload /></el-icon>
              全文导入
            </el-button>

            <el-button class="header-action" size="large" @click="openCrawlDialog">
              <el-icon><Download /></el-icon>
              小说爬取
            </el-button>

            <el-button class="primary-button" type="primary" size="large" @click="openCreateDialog">
              <el-icon><Plus /></el-icon>
              新建章节
            </el-button>
          </div>
        </header>

        <section class="toolbar">
          <el-input
            v-model="searchKeyword"
            class="search-input"
            clearable
            placeholder="按章节标题搜索"
            @clear="handleSearchClear"
            @keyup.enter="handleSearchSubmit"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <div class="toolbar-spacer"></div>

          <el-button
            :disabled="selectedRows.length === 0 || cleaning"
            :loading="cleaning"
            @click="batchCleanSelected"
          >
            <el-icon><MagicStick /></el-icon>
            清洗事件 ({{ selectedRows.length }})
          </el-button>

          <el-button
            :disabled="selectedRows.length === 0"
            type="danger"
            @click="batchDeleteSelected"
          >
            <el-icon><Delete /></el-icon>
            批量删除
          </el-button>
        </section>

        <section class="table-wrap">
          <el-table
            v-loading="loading"
            :data="pagedNovels"
            class="novel-table"
            element-loading-background="rgba(13, 17, 23, 0.55)"
            row-key="id"
            stripe
            :tooltip-options="{ effect: 'dark', popperClass: 'novel-cell-tooltip' }"
            @selection-change="onSelectionChange"
          >
            <el-table-column type="selection" width="48" />

            <el-table-column prop="chapterIndex" label="序号" width="80">
              <template #default="{ row }">
                <span class="row-index">#{{ row.chapterIndex }}</span>
              </template>
            </el-table-column>

            <el-table-column prop="reel" label="卷次" width="140">
              <template #default="{ row }">
                <el-tag class="reel-tag" effect="plain" round>{{ row.reel || '未分卷' }}</el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="chapter" label="章节标题" min-width="220" show-overflow-tooltip />

            <el-table-column label="字数" width="100">
              <template #default="{ row }">
                <span class="row-count">{{ (row.chapterData || '').length }}</span>
              </template>
            </el-table-column>

            <el-table-column label="事件状态" width="160">
              <template #default="{ row }">
                <span class="status-chip" :class="`status-chip--${statusKey(row.eventState)}`">
                  <span class="status-dot"></span>
                  {{ statusLabel(row.eventState) }}
                </span>
              </template>
            </el-table-column>

            <el-table-column label="操作" width="220" align="right">
              <template #default="{ row }">
                <el-tooltip content="查看" placement="top">
                  <el-button text circle class="icon-action" @click="openViewDrawer(row)">
                    <el-icon><View /></el-icon>
                  </el-button>
                </el-tooltip>

                <el-tooltip content="清洗事件" placement="top">
                  <el-button
                    text
                    circle
                    class="icon-action"
                    :disabled="row.eventState === 0 && row.cleaningInline"
                    @click="cleanSingle(row)"
                  >
                    <el-icon><MagicStick /></el-icon>
                  </el-button>
                </el-tooltip>

                <el-tooltip content="编辑" placement="top">
                  <el-button text circle class="icon-action" @click="openEditDialog(row)">
                    <el-icon><EditPen /></el-icon>
                  </el-button>
                </el-tooltip>

                <el-tooltip content="删除" placement="top">
                  <el-button text circle class="icon-action delete" @click="handleDelete(row)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-tooltip>
              </template>
            </el-table-column>

            <template #empty>
              <el-empty description="该项目暂无章节，点击右上角新建" />
            </template>
          </el-table>
        </section>

        <div class="pagination-wrap">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="totalNovels"
            layout="prev, pager, next, total"
            background
          />
        </div>
      </section>
    </div>

    <!-- 新增 / 编辑章节 -->
    <el-dialog
      v-model="formDialogVisible"
      :title="formDialogTitle"
      width="780px"
      destroy-on-close
      class="novel-dark-dialog"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        class="novel-form"
        label-position="top"
      >
        <div class="form-grid">
          <el-form-item label="章节序号" prop="chapterIndex">
            <el-input-number v-model="form.chapterIndex" :min="1" :max="9999" />
          </el-form-item>

          <el-form-item label="卷次" prop="reel">
            <el-input v-model="form.reel" placeholder="如：第一卷 · 风起" maxlength="60" />
          </el-form-item>
        </div>

        <el-form-item label="章节标题" prop="chapter">
          <el-input v-model="form.chapter" placeholder="如：第十二章 · 山雨欲来" maxlength="120" show-word-limit />
        </el-form-item>

        <el-form-item label="章节正文" prop="chapterData">
          <el-input
            v-model="form.chapterData"
            type="textarea"
            :rows="10"
            placeholder="粘贴章节正文（建议 500 字以上以便清洗事件）"
            maxlength="20000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item v-if="formMode === 'edit'" label="清洗事件（可选编辑）" prop="event">
          <el-input
            v-model="form.event"
            type="textarea"
            :rows="6"
            placeholder="保存后系统会自动重新清洗，也可在此手动覆写"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 章节预览 / 事件清洗结果 -->
    <el-drawer
      v-model="viewDrawerVisible"
      :title="viewDrawerTitle"
      direction="rtl"
      size="62%"
      class="novel-dark-drawer"
    >
      <div v-if="viewingNovel" class="view-stack">
        <div class="view-field">
          <label class="view-field__label">章节名称</label>
          <div class="view-field__value view-field__value--single">
            {{ viewingNovel.chapter }}
          </div>
        </div>

        <div class="view-field">
          <div class="view-field__label-row">
            <label class="view-field__label">事件内容</label>
            <span class="status-chip" :class="`status-chip--${statusKey(viewingNovel.eventState)}`">
              <span class="status-dot"></span>
              {{ statusLabel(viewingNovel.eventState) }}
            </span>
          </div>

          <div v-if="viewingNovel.eventState === 1" class="view-field__value view-event">
            {{ viewingNovel.event }}
          </div>
          <div v-else-if="viewingNovel.eventState === -1" class="view-field__value view-error">
            <p>清洗失败：</p>
            <p>{{ viewingNovel.errorReason || '未知错误' }}</p>
          </div>
          <div v-else class="view-field__value view-empty">
            <el-empty description="尚未清洗，点击下方按钮生成事件" />
          </div>
        </div>

        <div class="view-field view-field--grow">
          <div class="view-field__label-row">
            <label class="view-field__label">章节内容</label>
            <span class="view-field__hint">{{ (viewingNovel.chapterData || '').length }} 字</span>
          </div>
          <div class="view-field__value view-text">
            <p
              v-for="(paragraph, idx) in splitParagraphs(viewingNovel.chapterData)"
              :key="idx"
            >
              {{ paragraph }}
            </p>
          </div>
        </div>

        <div class="view-actions">
          <el-button
            type="primary"
            :loading="viewingNovel.cleaningInline"
            @click="cleanSingle(viewingNovel)"
          >
            <el-icon><MagicStick /></el-icon>
            {{ viewingNovel.eventState === 1 ? '重新清洗' : '生成事件' }}
          </el-button>
        </div>
      </div>
    </el-drawer>

    <NovelImportDialog
      v-model="importDialogVisible"
      :project-public-id="projectPublicId"
      @submit="handleImportSubmit"
    />

    <Settings v-model="settingsVisible" />
  </main>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { AxiosError } from 'axios'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Connection,
  Delete,
  Document,
  Download,
  EditPen,
  Folder,
  List,
  MagicStick,
  Plus,
  Reading,
  Search,
  Setting,
  Upload,
  View,
} from '@element-plus/icons-vue'
import {
  batchCleanNovelChaptersApi,
  batchDeleteNovelChaptersApi,
  cleanNovelChapterApi,
  createNovelChapterApi,
  deleteNovelChapterApi,
  importNovelChaptersApi,
  listNovelChaptersApi,
  updateNovelChapterApi,
  type EventState,
  type NovelChapterImportItemPayload,
  type NovelChapterPayload,
  type NovelChapterRecord,
} from '@/api/novel'
import NovelImportDialog from '../components/NovelImportDialog.vue'
import Settings from '../components/Settings.vue'

interface NovelChapter extends NovelChapterRecord {
  cleaningInline?: boolean
}

interface NovelChapterForm {
  chapterIndex: number
  reel: string
  chapter: string
  chapterData: string
  event: string
}

interface ImportChapterDraft {
  reel: string
  chapter: string
  chapterData: string
}

const router = useRouter()
const route = useRoute()
const formRef = ref<FormInstance>()

const projectPublicId = ref('')
const novels = ref<NovelChapter[]>([])
const totalNovels = ref(0)
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(8)
const loading = ref(false)
const cleaning = ref(false)
const submitting = ref(false)

const selectedRows = ref<NovelChapter[]>([])

const formDialogVisible = ref(false)
const formMode = ref<'create' | 'edit'>('create')
const editingId = ref<number | null>(null)

const viewDrawerVisible = ref(false)
const viewingNovelId = ref<number | null>(null)

const settingsVisible = ref(false)

const form = reactive<NovelChapterForm>({
  chapterIndex: 1,
  reel: '',
  chapter: '',
  chapterData: '',
  event: '',
})

const formRules: FormRules<NovelChapterForm> = {
  chapter: [{ required: true, message: '请输入章节标题', trigger: 'blur' }],
  chapterData: [{ required: true, message: '请输入章节正文', trigger: 'blur' }],
  chapterIndex: [{ required: true, message: '请填写章节序号', trigger: 'blur' }],
}

const pagedNovels = computed(() => novels.value)

const formDialogTitle = computed(() => (formMode.value === 'create' ? '新建章节' : '编辑章节'))

const viewingNovel = computed(() =>
  viewingNovelId.value ? novels.value.find((item) => item.id === viewingNovelId.value) ?? null : null,
)

const viewDrawerTitle = computed(() => (viewingNovel.value ? `章节预览：${viewingNovel.value.chapter}` : '章节预览'))

const fetchNovels = async () => {
  if (!projectPublicId.value) return
  loading.value = true
  try {
    const { data } = await listNovelChaptersApi(projectPublicId.value, {
      page: currentPage.value,
      limit: pageSize.value,
      search: searchKeyword.value.trim() || undefined,
    })
    const lastPage = Math.max(1, Math.ceil(data.total / pageSize.value))
    if (data.total > 0 && data.data.length === 0 && currentPage.value > lastPage) {
      currentPage.value = lastPage
      return
    }
    novels.value = data.data.map((item) => ({ ...item }))
    totalNovels.value = data.total
    selectedRows.value = []
  } catch (error) {
    ElMessage.error(`章节加载失败：${getErrorMessage(error)}`)
  } finally {
    loading.value = false
  }
}

const statusKey = (state: EventState) => {
  if (state === 1) return 'success'
  if (state === -1) return 'error'
  return 'pending'
}

const statusLabel = (state: EventState) => {
  if (state === 1) return '已生成'
  if (state === -1) return '清洗失败'
  return '待清洗'
}

const splitParagraphs = (raw: string) => (raw || '').split(/\n+/).filter(Boolean)

const onSelectionChange = (rows: NovelChapter[]) => {
  selectedRows.value = rows
}

const nextChapterIndex = () => {
  if (novels.value.length === 0) return totalNovels.value + 1
  return Math.max(...novels.value.map((item) => item.chapterIndex)) + 1
}

const resetForm = () => {
  form.chapterIndex = nextChapterIndex()
  form.reel = ''
  form.chapter = ''
  form.chapterData = ''
  form.event = ''
}

const openCreateDialog = () => {
  if (!ensureProjectReady()) return
  formMode.value = 'create'
  editingId.value = null
  resetForm()
  formDialogVisible.value = true
}

const openEditDialog = (row: NovelChapter) => {
  if (!ensureProjectReady()) return
  formMode.value = 'edit'
  editingId.value = row.id
  form.chapterIndex = row.chapterIndex
  form.reel = row.reel
  form.chapter = row.chapter
  form.chapterData = row.chapterData
  form.event = row.event
  formDialogVisible.value = true
}

const submitForm = async () => {
  if (!formRef.value || !ensureProjectReady()) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload = buildFormPayload()
    if (formMode.value === 'create') {
      await createNovelChapterApi(projectPublicId.value, payload)
      ElMessage.success('章节已新建')
      const nextPage = Math.max(1, Math.ceil((totalNovels.value + 1) / pageSize.value))
      if (currentPage.value === nextPage) {
        await fetchNovels()
      } else {
        currentPage.value = nextPage
      }
    } else if (editingId.value !== null) {
      await updateNovelChapterApi(projectPublicId.value, editingId.value, payload)
      ElMessage.success('章节已更新')
      await fetchNovels()
    }
    formDialogVisible.value = false
  } catch (error) {
    ElMessage.error(`保存失败：${getErrorMessage(error)}`)
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (row: NovelChapter) => {
  if (!ensureProjectReady()) return
  try {
    await ElMessageBox.confirm(`确定删除「${row.chapter}」吗？删除后不可恢复。`, '删除章节', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger',
      customClass: 'novel-dark-messagebox',
    })
    await deleteNovelChapterApi(projectPublicId.value, row.id)
    if (viewingNovelId.value === row.id) {
      viewDrawerVisible.value = false
      viewingNovelId.value = null
    }
    ElMessage.success('章节已删除')
    await fetchNovels()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error(`删除失败：${getErrorMessage(error)}`)
  }
}

const batchDeleteSelected = async () => {
  if (!ensureProjectReady() || selectedRows.value.length === 0) return
  try {
    await ElMessageBox.confirm(`确定批量删除 ${selectedRows.value.length} 个章节吗？`, '批量删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger',
      customClass: 'novel-dark-messagebox',
    })
    const ids = selectedRows.value.map((row) => row.id)
    await batchDeleteNovelChaptersApi(projectPublicId.value, { ids })
    if (viewingNovelId.value && ids.includes(viewingNovelId.value)) {
      viewDrawerVisible.value = false
      viewingNovelId.value = null
    }
    selectedRows.value = []
    ElMessage.success('选中章节已删除')
    await fetchNovels()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error(`批量删除失败：${getErrorMessage(error)}`)
  }
}

const cleanSingle = async (row: NovelChapter) => {
  if (!ensureProjectReady() || row.cleaningInline) return
  row.cleaningInline = true
  try {
    const { data } = await cleanNovelChapterApi(projectPublicId.value, row.id)
    replaceChapter({ ...data, cleaningInline: false })
    if (data.eventState === 1) {
      ElMessage.success(`「${data.chapter}」事件已生成`)
    } else {
      ElMessage.warning(data.errorReason || `「${data.chapter}」暂未生成事件`)
    }
  } catch (error) {
    row.cleaningInline = false
    ElMessage.error(`清洗失败：${getErrorMessage(error)}`)
  }
}

const batchCleanSelected = async () => {
  if (!ensureProjectReady() || selectedRows.value.length === 0) return
  cleaning.value = true
  const ids = selectedRows.value.map((row) => row.id)
  markRowsCleaning(ids, true)
  try {
    await batchCleanNovelChaptersApi(projectPublicId.value, { ids })
    selectedRows.value = []
    ElMessage.success(`已清洗 ${ids.length} 个章节`)
    await fetchNovels()
  } catch (error) {
    ElMessage.error(`批量清洗失败：${getErrorMessage(error)}`)
  } finally {
    markRowsCleaning(ids, false)
    cleaning.value = false
  }
}

const openViewDrawer = (row: NovelChapter) => {
  viewingNovelId.value = row.id
  viewDrawerVisible.value = true
}

const goProject = () => {
  router.push('/project')
}

const showComingSoon = () => {
  ElMessage.info('功能开发中')
}

const importDialogVisible = ref(false)
const openImportDialog = () => {
  if (!ensureProjectReady()) return
  importDialogVisible.value = true
}

const handleImportSubmit = async (drafts: ImportChapterDraft[]) => {
  if (!ensureProjectReady() || drafts.length === 0) return
  const chapters: NovelChapterImportItemPayload[] = drafts
    .map((draft) => ({
      reel: draft.reel.trim(),
      chapter: draft.chapter.trim(),
      chapterData: draft.chapterData.trim(),
    }))
    .filter((draft) => draft.chapter && draft.chapterData)
  if (chapters.length === 0) {
    ElMessage.warning('没有可导入的章节正文')
    return
  }
  try {
    const { data } = await importNovelChaptersApi(projectPublicId.value, { chapters })
    const importedCount = data.length
    ElMessage.success(`已导入 ${importedCount} 个章节`)
    currentPage.value = Math.max(1, Math.ceil((totalNovels.value + importedCount) / pageSize.value))
    await fetchNovels()
  } catch (error) {
    ElMessage.error(`全文导入失败：${getErrorMessage(error)}`)
  }
}

const openCrawlDialog = () => {
  ElMessage.info('功能开发中')
}

const handleSearchClear = () => {
  searchKeyword.value = ''
}

const handleSearchSubmit = () => {
  runSearchNow()
}

const buildFormPayload = (): NovelChapterPayload => ({
  chapterIndex: form.chapterIndex,
  reel: form.reel.trim(),
  chapter: form.chapter.trim(),
  chapterData: form.chapterData.trim(),
  event: form.event.trim(),
})

const replaceChapter = (chapter: NovelChapter) => {
  const index = novels.value.findIndex((item) => item.id === chapter.id)
  if (index >= 0) {
    novels.value.splice(index, 1, chapter)
  }
}

const markRowsCleaning = (ids: number[], value: boolean) => {
  const idSet = new Set(ids)
  novels.value.forEach((item) => {
    if (idSet.has(item.id)) {
      item.cleaningInline = value
    }
  })
}

const ensureProjectReady = () => {
  if (projectPublicId.value) return true
  ElMessage.warning('未指定项目')
  router.push('/project')
  return false
}

const resolveProjectPublicId = () => {
  const id = route.query.id
  if (Array.isArray(id)) return id[0] || ''
  return typeof id === 'string' ? id : ''
}

const loadRouteProject = () => {
  const id = resolveProjectPublicId().trim()
  if (!id) {
    ElMessage.warning('未指定项目')
    router.push('/project')
    return
  }
  if (projectPublicId.value !== id) {
    projectPublicId.value = id
    novels.value = []
    totalNovels.value = 0
    selectedRows.value = []
  }
  if (currentPage.value !== 1) {
    currentPage.value = 1
  } else {
    void fetchNovels()
  }
}

const runSearchNow = () => {
  if (searchTimer !== undefined) {
    window.clearTimeout(searchTimer)
    searchTimer = undefined
  }
  if (currentPage.value !== 1) {
    currentPage.value = 1
  } else {
    void fetchNovels()
  }
}

const getErrorMessage = (error: unknown) => {
  const axiosError = isRecord(error) ? (error as unknown as AxiosError<{ detail?: unknown; message?: unknown }>) : null
  const responseMessage =
    formatErrorDetail(axiosError?.response?.data?.detail) ||
    formatErrorDetail(axiosError?.response?.data?.message)
  if (responseMessage) return responseMessage
  if (error instanceof Error && error.message) return error.message
  return formatErrorDetail(error) || '请求失败'
}

const formatErrorDetail = (detail: unknown): string => {
  if (!detail) return ''
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map(formatErrorDetail).filter(Boolean).join('；')
  }
  if (isRecord(detail)) {
    const record = detail as Record<string, unknown>
    const message = formatErrorDetail(record.msg) || formatErrorDetail(record.message) || formatErrorDetail(record.detail)
    const location = Array.isArray(record.loc) ? record.loc.map(String).join('.') : ''
    if (message) return location ? `${location}: ${message}` : message
    try {
      return JSON.stringify(detail)
    } catch {
      return String(detail)
    }
  }
  return String(detail)
}

const isRecord = (value: unknown): value is Record<string, unknown> => (
  typeof value === 'object' && value !== null
)

let searchTimer: number | undefined

watch(() => route.query.id, loadRouteProject, { immediate: true })

watch(currentPage, () => {
  void fetchNovels()
})

watch(searchKeyword, () => {
  if (searchTimer !== undefined) {
    window.clearTimeout(searchTimer)
  }
  searchTimer = window.setTimeout(() => {
    runSearchNow()
  }, 300)
})
</script>

<style scoped>
.novel-page {
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  padding: 16px;
  color: #e6edf3;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
  background:
    radial-gradient(circle at top, rgba(100, 116, 139, 0.18) 0%, rgba(11, 13, 16, 0) 32%),
    linear-gradient(180deg, #0d1117 0%, #0b0d10 100%);
}

.app-shell {
  height: calc(100vh - 32px);
  height: calc(100dvh - 32px);
  display: grid;
  grid-template-columns: 84px 1fr;
  gap: 16px;
}

.sidebar {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  padding: 18px 0;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.015));
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.45);
}

.side-top,
.side-bottom {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.brand {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  color: #0a0a0a;
  font-size: 20px;
  font-weight: 800;
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
  cursor: pointer;
  user-select: none;
  background: linear-gradient(135deg, #f3d96b, #c4b5fd);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.45),
    0 6px 18px rgba(243, 217, 107, 0.18);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.brand:hover {
  transform: translateY(-1px);
}

.nav-btn {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border: 1px solid transparent;
  border-radius: 16px;
  color: #8b949e;
  background: transparent;
  cursor: pointer;
  font-size: 22px;
  transition: color 0.2s ease, background 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}

.nav-btn :deep(.el-icon) {
  font-size: 22px;
}

.nav-btn:hover {
  color: #e6edf3;
  background: rgba(255, 255, 255, 0.05);
  transform: translateY(-1px);
}

.nav-btn.active {
  color: #dbeafe;
  border-color: rgba(37, 99, 235, 0.32);
  background: linear-gradient(180deg, rgba(37, 99, 235, 0.22), rgba(37, 99, 235, 0.12));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.main-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 24px 28px 20px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.025), rgba(255, 255, 255, 0.015));
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.45);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 18px;
  flex-shrink: 0;
}

.page-header__right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  margin: 0;
  font-size: 32px;
  line-height: 1.1;
  font-weight: 800;
  background: linear-gradient(180deg, #ffffff 0%, #93a1b3 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.desc {
  margin: 6px 0 0;
  color: #8b949e;
  font-size: 13px;
  line-height: 1.4;
}

.project-select {
  width: 220px;
}

.project-select :deep(.el-select__wrapper) {
  height: 38px;
  background-color: rgba(255, 255, 255, 0.04);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.08) inset;
  border-radius: 10px;
  color: #e6edf3;
}

.project-select :deep(.el-select__wrapper:hover) {
  background-color: rgba(255, 255, 255, 0.06);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.18) inset;
}

.project-select :deep(.el-select__wrapper.is-focused) {
  background-color: rgba(37, 99, 235, 0.08);
  box-shadow: 0 0 0 1px #2563eb inset;
}

.project-select :deep(.el-select__placeholder),
.project-select :deep(.el-select__selected-item) {
  color: #e6edf3;
}

.primary-button {
  height: 38px;
  padding: 0 16px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  background: #2563eb;
  box-shadow: 0 8px 18px rgba(37, 99, 235, 0.18);
  transition: background 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.primary-button :deep(.el-icon) {
  margin-right: 0;
  font-size: 16px;
}

.primary-button:hover,
.primary-button:focus {
  background: #1d4ed8;
  box-shadow: 0 14px 30px rgba(37, 99, 235, 0.28);
  transform: translateY(-1px);
}

.header-action {
  height: 38px;
  padding: 0 14px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  color: #c5cdd6;
  background-color: rgba(255, 255, 255, 0.04);
  transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease, transform 0.2s ease;
}

.header-action :deep(.el-icon) {
  margin-right: 0;
  font-size: 16px;
}

.header-action:hover,
.header-action:focus {
  background-color: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.18);
  color: #ffffff;
  transform: translateY(-1px);
}

.header-action:active {
  transform: translateY(0);
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.toolbar-spacer {
  flex: 1;
}

.search-input {
  max-width: 360px;
}

.toolbar :deep(.el-input__wrapper) {
  background-color: rgba(255, 255, 255, 0.04);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.08) inset;
  border-radius: 10px;
  transition: box-shadow 0.18s ease, background-color 0.18s ease;
}

.toolbar :deep(.el-input__wrapper:hover) {
  background-color: rgba(255, 255, 255, 0.06);
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.18) inset;
}

.toolbar :deep(.el-input__wrapper.is-focus) {
  background-color: rgba(37, 99, 235, 0.08);
  box-shadow: 0 0 0 1px #2563eb inset;
}

.toolbar :deep(.el-input__inner) {
  color: #e6edf3;
}

.toolbar :deep(.el-input__inner::placeholder) {
  color: #6e7681;
}

.toolbar :deep(.el-input__prefix-inner .el-icon),
.toolbar :deep(.el-input__suffix-inner .el-icon) {
  color: #8b949e;
}

.toolbar :deep(.el-button) {
  height: 38px;
  padding: 0 16px;
  border-radius: 10px;
  background-color: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
  color: #c5cdd6;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.toolbar :deep(.el-button:hover:not(.is-disabled)) {
  background-color: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.18);
  color: #ffffff;
}

.toolbar :deep(.el-button.el-button--danger.is-plain) {
  background-color: rgba(248, 113, 113, 0.08);
  border-color: rgba(248, 113, 113, 0.32);
  color: #fca5a5;
}

.toolbar :deep(.el-button.el-button--danger.is-plain:hover:not(.is-disabled)) {
  background-color: rgba(248, 113, 113, 0.18);
  border-color: rgba(248, 113, 113, 0.45);
  color: #fecaca;
}

.toolbar :deep(.el-button.is-disabled) {
  opacity: 0.5;
  cursor: not-allowed;
}

.table-wrap {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.015);
}

.novel-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(255, 255, 255, 0.04);
  --el-table-border-color: rgba(255, 255, 255, 0.06);
  --el-table-border: 1px solid rgba(255, 255, 255, 0.06);
  --el-table-header-text-color: #c5cdd6;
  --el-table-text-color: #c5cdd6;
  --el-table-row-hover-bg-color: rgba(37, 99, 235, 0.08);
  background: transparent;
  height: 100%;
}

.novel-table :deep(thead th.el-table__cell) {
  background-color: rgba(255, 255, 255, 0.04);
  color: #c5cdd6;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.novel-table :deep(td.el-table__cell),
.novel-table :deep(th.el-table__cell) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  background: transparent;
}

.novel-table :deep(tr.el-table__row--striped td.el-table__cell) {
  background: rgba(255, 255, 255, 0.012);
}

.novel-table :deep(tbody tr:hover > td.el-table__cell) {
  background-color: rgba(37, 99, 235, 0.08) !important;
}

.novel-table :deep(.el-checkbox__inner) {
  background-color: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.18);
}

.novel-table :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #2563eb;
  border-color: #2563eb;
}

.novel-table :deep(.el-scrollbar__thumb) {
  background-color: rgba(255, 255, 255, 0.18);
  border-radius: 999px;
  transition: background-color 0.18s ease;
}

.novel-table :deep(.el-scrollbar__thumb:hover) {
  background-color: rgba(255, 255, 255, 0.32);
}

.novel-table :deep(.el-scrollbar__bar.is-horizontal) {
  display: none;
}

.novel-table :deep(.el-scrollbar__wrap) {
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.14) transparent;
}

.novel-table :deep(.el-scrollbar__wrap::-webkit-scrollbar) {
  width: 6px;
  height: 0;
}

.novel-table :deep(.el-scrollbar__wrap::-webkit-scrollbar-track) {
  background: transparent;
}

.novel-table :deep(.el-scrollbar__wrap::-webkit-scrollbar-thumb) {
  background-color: rgba(255, 255, 255, 0.12);
  border-radius: 999px;
}

.novel-table :deep(.el-scrollbar__wrap::-webkit-scrollbar-thumb:hover) {
  background-color: rgba(255, 255, 255, 0.24);
}

.row-index {
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
  color: #93c5fd;
  font-size: 13px;
  font-weight: 600;
}

.row-count {
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
  color: #8b949e;
  font-size: 12px;
}

.reel-tag {
  height: 24px;
  padding: 0 10px;
  font-size: 11px;
  font-weight: 500;
  color: #c4b5fd;
  border-color: rgba(167, 139, 250, 0.32);
  background: rgba(167, 139, 250, 0.12);
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
  border: 1px solid transparent;
}

.status-chip .status-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  display: inline-block;
}

.status-chip--success {
  color: #86efac;
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.32);
}

.status-chip--success .status-dot {
  background: #22c55e;
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.6);
}

.status-chip--pending {
  color: #fde68a;
  background: rgba(234, 179, 8, 0.1);
  border-color: rgba(234, 179, 8, 0.32);
}

.status-chip--pending .status-dot {
  background: #eab308;
  box-shadow: 0 0 6px rgba(234, 179, 8, 0.6);
}

.status-chip--error {
  color: #fca5a5;
  background: rgba(248, 113, 113, 0.1);
  border-color: rgba(248, 113, 113, 0.32);
}

.status-chip--error .status-dot {
  background: #f87171;
  box-shadow: 0 0 6px rgba(248, 113, 113, 0.6);
}

.icon-action {
  width: 30px;
  height: 30px;
  font-size: 15px;
  color: #8b949e;
  border-radius: 8px;
  --el-fill-color-light: transparent;
  --el-fill-color: transparent;
  --el-color-info: #93c5fd;
  transition: color 0.2s ease, background-color 0.2s ease, transform 0.2s ease;
}

.icon-action :deep(.el-icon) {
  font-size: 15px;
}

.icon-action:hover,
.icon-action:focus {
  color: #93c5fd;
  background-color: rgba(59, 130, 246, 0.14);
  transform: translateY(-1px);
}

.icon-action.delete {
  --el-color-info: #fca5a5;
}

.icon-action.delete:hover,
.icon-action.delete:focus {
  color: #fca5a5;
  background-color: rgba(248, 113, 113, 0.16);
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 14px;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

.pagination-wrap :deep(.el-pagination.is-background .btn-prev),
.pagination-wrap :deep(.el-pagination.is-background .btn-next),
.pagination-wrap :deep(.el-pagination.is-background .el-pager li) {
  color: #8b949e;
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
  font-size: 13px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.02);
}

.pagination-wrap :deep(.el-pagination.is-background .el-pager li.is-active) {
  color: #fff;
  border-color: #2563eb;
  background: #2563eb;
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.22);
}

.pagination-wrap :deep(.el-pagination__total) {
  color: #8b949e;
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
  font-size: 13px;
}

.novel-form {
  padding-right: 8px;
}

.form-grid {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 0 18px;
}

.view-stack {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 4px;
  height: 100%;
  min-height: 0;
}

.view-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
}

.view-field--grow {
  flex: 1;
  min-height: 220px;
}

.view-field__label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.view-field__label {
  font-size: 13px;
  font-weight: 600;
  color: #d5dce4;
  letter-spacing: 0.2px;
}

.view-field__hint {
  font-size: 12px;
  color: #6e7681;
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
}

.view-field__value {
  padding: 12px 14px;
  border-radius: 10px;
  background-color: #0c1015;
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #e6edf3;
  font-size: 14px;
  line-height: 1.7;
}

.view-field__value--single {
  padding: 10px 14px;
  min-height: 42px;
  display: flex;
  align-items: center;
}

.view-field__value.view-empty {
  padding: 8px 0;
  background: transparent;
  border: 1px dashed rgba(255, 255, 255, 0.08);
}

.view-empty :deep(.el-empty) {
  --el-empty-padding: 10px 0;
  --el-empty-description-margin-top: 8px;
}

.view-empty :deep(.el-empty__image) {
  width: 56px;
}

.view-empty :deep(.el-empty__description p) {
  color: #8b949e;
  font-size: 12px;
}

.view-text {
  flex: 1;
  overflow-y: auto;
  color: #c5cdd6;
  font-size: 14px;
  line-height: 1.8;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.14) transparent;
}

.view-text::-webkit-scrollbar,
.view-event::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.view-text::-webkit-scrollbar-track,
.view-event::-webkit-scrollbar-track {
  background: transparent;
}

.view-text::-webkit-scrollbar-thumb,
.view-event::-webkit-scrollbar-thumb {
  background-color: rgba(255, 255, 255, 0.12);
  border-radius: 999px;
  transition: background-color 0.18s ease;
}

.view-text::-webkit-scrollbar-thumb:hover,
.view-event::-webkit-scrollbar-thumb:hover {
  background-color: rgba(255, 255, 255, 0.24);
}

.view-text::-webkit-scrollbar-corner,
.view-event::-webkit-scrollbar-corner {
  background: transparent;
}

.view-text p {
  margin: 0 0 12px;
}

.view-text p:last-child {
  margin-bottom: 0;
}

.view-event {
  max-height: 200px;
  overflow-y: auto;
  color: #d5dce4;
  font-size: 13px;
  line-height: 1.7;
  background: rgba(34, 197, 94, 0.04);
  border-color: rgba(34, 197, 94, 0.22);
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
  white-space: pre-wrap;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.14) transparent;
}

.view-error {
  background: rgba(248, 113, 113, 0.06);
  border-color: rgba(248, 113, 113, 0.22);
  color: #fca5a5;
  font-size: 13px;
  line-height: 1.7;
}

.view-error p {
  margin: 0 0 6px;
}

.view-error p:last-child {
  margin-bottom: 0;
}

.view-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 6px;
}

.view-actions :deep(.el-button) {
  border-radius: 10px;
}

@media (max-width: 1080px) {
  .view-field--grow {
    min-height: 180px;
  }
}

@media (max-width: 820px) {
  .app-shell {
    grid-template-columns: 1fr;
    gap: 14px;
  }

  .sidebar {
    flex-direction: row;
    padding: 12px 14px;
  }

  .side-top,
  .side-bottom {
    width: auto;
    flex-direction: row;
    gap: 10px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .page-header__right {
    flex-direction: column;
    align-items: stretch;
  }

  .project-select {
    width: 100%;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<style>
/* novel 页专用暗色弹窗、下拉与抽屉（element-plus teleport 到 body，需置于非 scoped 块） */
.novel-dark-dialog {
  background: linear-gradient(180deg, #12161b 0%, #0f141a 100%);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 24px;
  box-shadow: 0 30px 90px rgba(0, 0, 0, 0.55);
  overflow: hidden;
  color: #e6edf3;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
}

.novel-dark-dialog .el-dialog__header {
  margin: 0;
  padding: 22px 28px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.novel-dark-dialog .el-dialog__title {
  color: #f2f4f8;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.4px;
}

.novel-dark-dialog .el-dialog__headerbtn {
  top: 16px;
  right: 20px;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.02);
}

.novel-dark-dialog .el-dialog__headerbtn .el-dialog__close {
  color: #8b949e;
  font-size: 20px;
}

.novel-dark-dialog .el-dialog__headerbtn:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.18);
}

.novel-dark-dialog .el-dialog__headerbtn:hover .el-dialog__close {
  color: #ffffff;
}

.novel-dark-dialog .el-dialog__body {
  padding: 22px 28px 8px;
  color: #b8c2cc;
  max-height: calc(100vh - 240px);
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.14) transparent;
}

.novel-dark-dialog .el-dialog__body::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.novel-dark-dialog .el-dialog__body::-webkit-scrollbar-track {
  background: transparent;
}

.novel-dark-dialog .el-dialog__body::-webkit-scrollbar-thumb {
  background-color: rgba(255, 255, 255, 0.12);
  border-radius: 999px;
  transition: background-color 0.18s ease;
}

.novel-dark-dialog .el-dialog__body::-webkit-scrollbar-thumb:hover {
  background-color: rgba(255, 255, 255, 0.24);
}

.novel-dark-dialog .el-dialog__footer {
  padding: 16px 28px 22px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.novel-dark-dialog .el-form-item__label {
  color: #d5dce4;
  font-size: 14px;
  font-weight: 600;
  padding: 0 0 8px;
}

.novel-dark-dialog .el-input__wrapper,
.novel-dark-dialog .el-select__wrapper,
.novel-dark-dialog .el-input-number .el-input__wrapper {
  min-height: 42px;
  padding: 0 14px;
  background-color: #0c1015;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.12) inset;
  border-radius: 10px;
  color: #e6edf3;
  font-size: 14px;
}

.novel-dark-dialog .el-textarea__inner {
  min-height: 120px;
  padding: 12px 14px;
  background-color: #0c1015;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.12) inset;
  border: none;
  border-radius: 10px;
  color: #e6edf3;
  font-size: 14px;
  line-height: 1.65;
  font-family: inherit;
  resize: vertical;
}

.novel-dark-dialog .el-input__wrapper:hover,
.novel-dark-dialog .el-textarea__inner:hover,
.novel-dark-dialog .el-select__wrapper:hover {
  background-color: #0e131a;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.22) inset;
}

.novel-dark-dialog .el-input__wrapper.is-focus,
.novel-dark-dialog .el-textarea__inner:focus,
.novel-dark-dialog .el-select__wrapper.is-focused {
  background-color: #0d1219;
  box-shadow:
    0 0 0 1px rgba(37, 99, 235, 0.55) inset,
    0 0 0 3px rgba(37, 99, 235, 0.12);
}

.novel-dark-dialog .el-input__inner,
.novel-dark-dialog .el-textarea__inner {
  color: #e6edf3;
}

.novel-dark-dialog .el-input__inner::placeholder,
.novel-dark-dialog .el-textarea__inner::placeholder {
  color: #7e8893;
}

.novel-dark-dialog .el-input__count,
.novel-dark-dialog .el-input__count-inner,
.novel-dark-dialog .el-input .el-input__count,
.novel-dark-dialog .el-textarea .el-input__count {
  color: #6e7681 !important;
  background: transparent !important;
  background-color: transparent !important;
  font-size: 12px;
}

.novel-dark-dialog .el-textarea .el-input__count {
  bottom: 8px;
  right: 12px;
}

.novel-dark-dialog .el-dialog__footer .el-button {
  height: 40px;
  min-width: 88px;
  padding: 0 20px;
  border-radius: 10px;
  font-weight: 700;
}

.novel-dark-dialog .el-dialog__footer .el-button:not(.el-button--primary) {
  background-color: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.12);
  color: #e6edf3;
}

.novel-dark-dialog .el-dialog__footer .el-button:not(.el-button--primary):hover {
  background-color: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.22);
  color: #ffffff;
}

.novel-dark-dialog .el-dialog__footer .el-button--primary {
  background-color: #2563eb;
  border-color: #2563eb;
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.18);
}

.novel-dark-dialog .el-dialog__footer .el-button--primary:hover {
  background-color: #1d4ed8;
  border-color: #1d4ed8;
}

/* select 浮层 */
.novel-dark-select.el-popper {
  background-color: #14181f;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.45);
  color: #e6edf3;
}

.novel-dark-select.el-popper .el-select-dropdown__list {
  padding: 6px 4px;
}

.novel-dark-select.el-popper .el-select-dropdown__item {
  color: #c5cdd6;
  border-radius: 8px;
  margin: 2px 4px;
  padding: 0 12px;
  height: 32px;
  line-height: 32px;
}

.novel-dark-select.el-popper .el-select-dropdown__item:hover,
.novel-dark-select.el-popper .el-select-dropdown__item.is-hovering {
  background-color: rgba(255, 255, 255, 0.06);
  color: #ffffff;
}

.novel-dark-select.el-popper .el-select-dropdown__item.is-selected {
  color: #93c5fd;
  background-color: rgba(37, 99, 235, 0.16);
  font-weight: 600;
}

.novel-dark-select.el-popper .el-popper__arrow::before {
  background-color: #14181f;
  border-color: rgba(255, 255, 255, 0.08);
}

/* multiple 模式下浮层选项的"已选" 状态（element-plus 多选下拉的勾选指示） */
.novel-dark-select.el-popper .el-select-dropdown__item.is-selected::after {
  color: #93c5fd;
}

/* multiple select 输入框内的已选 tag、折叠 tag 暗色风格 */
.novel-dark-dialog .el-select__wrapper .el-select__selected-item .el-tag,
.novel-dark-dialog .el-select .el-select__tags-text + .el-tag,
.novel-dark-dialog .el-select__wrapper .el-tag {
  background-color: rgba(37, 99, 235, 0.14);
  border-color: rgba(37, 99, 235, 0.4);
  color: #93c5fd;
  font-weight: 500;
}

.novel-dark-dialog .el-select__wrapper .el-tag .el-tag__close,
.novel-dark-dialog .el-select__wrapper .el-tag .el-icon {
  color: #93c5fd;
  background-color: transparent;
}

.novel-dark-dialog .el-select__wrapper .el-tag .el-tag__close:hover {
  background-color: rgba(37, 99, 235, 0.32);
  color: #ffffff;
}

/* collapse-tags-tooltip 浮层（鼠标 hover 已选 + N 标签时显示的全部已选项）暗色风格 */
.el-popper.is-dark.el-tooltip__popper.el-select__popper--multiple,
.el-popper.is-dark[role="tooltip"] {
  background: linear-gradient(180deg, #14181f 0%, #0d1117 100%);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #e6edf3;
}

.el-popper.is-dark[role="tooltip"] .el-popper__arrow::before {
  background: #14181f;
  border-color: rgba(255, 255, 255, 0.12);
}

/* el-table show-overflow-tooltip 浮层（章节标题超长时） */
.novel-cell-tooltip.el-popper {
  max-width: 520px;
  padding: 10px 14px;
  background: linear-gradient(180deg, #14181f 0%, #0d1117 100%);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.45);
  color: #e6edf3;
  font-size: 13px;
  line-height: 1.7;
}

.novel-cell-tooltip.el-popper .el-popper__arrow::before {
  background-color: #14181f;
  border-color: rgba(255, 255, 255, 0.12);
}

/* drawer 暗色 */
.novel-dark-drawer {
  background: linear-gradient(180deg, #12161b 0%, #0f141a 100%);
  border-left: 1px solid rgba(255, 255, 255, 0.08);
  color: #e6edf3;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
}

.novel-dark-drawer .el-drawer__header {
  margin: 0;
  padding: 22px 24px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  color: #f2f4f8;
  font-size: 18px;
  font-weight: 700;
}

.novel-dark-drawer .el-drawer__close-btn {
  color: #8b949e;
}

.novel-dark-drawer .el-drawer__close-btn:hover {
  color: #ffffff;
}

.novel-dark-drawer .el-drawer__body {
  padding: 18px 24px 24px;
  background: transparent;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.14) transparent;
}

.novel-dark-drawer .el-drawer__body::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.novel-dark-drawer .el-drawer__body::-webkit-scrollbar-track {
  background: transparent;
}

.novel-dark-drawer .el-drawer__body::-webkit-scrollbar-thumb {
  background-color: rgba(255, 255, 255, 0.12);
  border-radius: 999px;
  transition: background-color 0.18s ease;
}

.novel-dark-drawer .el-drawer__body::-webkit-scrollbar-thumb:hover {
  background-color: rgba(255, 255, 255, 0.24);
}

/* messagebox 暗色 */
.novel-dark-messagebox {
  background: linear-gradient(180deg, #14181f 0%, #0d1117 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.55);
  color: #e6edf3;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
}

.novel-dark-messagebox .el-message-box__header {
  padding: 18px 24px 8px;
}

.novel-dark-messagebox .el-message-box__title {
  color: #e6edf3;
  font-weight: 700;
}

.novel-dark-messagebox .el-message-box__content {
  padding: 8px 24px 18px;
  color: #b8c2cc;
}

.novel-dark-messagebox .el-message-box__btns {
  padding: 12px 24px 18px;
  background: rgba(255, 255, 255, 0.015);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.novel-dark-messagebox .el-message-box__btns .el-button {
  border-radius: 8px;
}

.novel-dark-messagebox .el-message-box__btns .el-button:not(.el-button--primary):not(.el-button--danger) {
  background-color: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
  color: #c5cdd6;
}

.novel-dark-messagebox .el-message-box__btns .el-button:not(.el-button--primary):not(.el-button--danger):hover {
  background-color: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.18);
  color: #ffffff;
}

</style>
