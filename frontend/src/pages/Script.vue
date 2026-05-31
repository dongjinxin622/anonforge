<template>
  <main class="script-page">
    <div class="app-shell">
      <aside class="sidebar">
        <div class="side-top">
          <div class="brand" @click="goProject">AF</div>

          <el-tooltip content="项目" placement="right">
            <button class="nav-btn" aria-label="项目" @click="goProject">
              <el-icon><Folder /></el-icon>
            </button>
          </el-tooltip>

          <el-tooltip content="剧本" placement="right">
            <button class="nav-btn active" aria-label="剧本">
              <el-icon><Tickets /></el-icon>
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
            <h1 class="title">我的剧本</h1>
            <p class="desc">管理项目剧本素材库、关联资产与短剧分镜原型</p>
          </div>

          <div class="page-header__right">
            <el-button class="header-action" size="large" @click="openBatchImportDialog">
              <el-icon><Upload /></el-icon>
              &nbsp;导入剧本
            </el-button>

            <el-button class="primary-button" type="primary" size="large" @click="openCreateDialog">
              <el-icon><Plus /></el-icon>
              &nbsp;新建剧本
            </el-button>
          </div>
        </header>

        <section class="toolbar">
          <el-input
            v-model="searchKeyword"
            class="search-input"
            clearable
            placeholder="按剧本名称搜索"
            @clear="searchKeyword = ''"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <el-dropdown
            trigger="click"
            placement="bottom-start"
            popper-class="script-sort-dropdown"
            @command="onSortCommand"
          >
            <el-button class="sort-trigger">
              <el-icon><Sort /></el-icon>
              &nbsp;排序：{{ currentSortLabel }}
              <el-icon class="sort-direction-icon">
                <CaretTop v-if="sortOrder === 'asc'" />
                <CaretBottom v-else />
              </el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item
                  v-for="opt in SORT_OPTIONS"
                  :key="opt.value"
                  :command="opt.value"
                  :class="{ 'is-active': sortField === opt.value }"
                >
                  <span class="sort-option-label">{{ opt.label }}</span>
                  <el-icon v-if="sortField === opt.value" class="sort-option-arrow">
                    <CaretTop v-if="sortOrder === 'asc'" />
                    <CaretBottom v-else />
                  </el-icon>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <div class="toolbar-spacer"></div>

          <el-button :disabled="scripts.length === 0" @click="toggleSelectAll">
            <el-icon><Select /></el-icon>
            &nbsp;{{ isAllSelected ? '取消全选' : '全选' }}
          </el-button>

          <el-button
            :disabled="selectedIds.length === 0 || extracting"
            :loading="extracting"
            @click="batchExtractAssets"
          >
            <el-icon><MagicStick /></el-icon>
            &nbsp;提取资产{{ selectedIds.length ? ` (${selectedIds.length})` : '' }}
          </el-button>

          <el-button
            :disabled="selectedIds.length === 0"
            @click="batchExportZip"
          >
            <el-icon><Download /></el-icon>
            &nbsp;导出剧本{{ selectedIds.length ? ` (${selectedIds.length})` : '' }}
          </el-button>

          <el-button
            :disabled="selectedIds.length === 0"
            type="danger"
            @click="batchDeleteSelected"
          >
            <el-icon><Delete /></el-icon>
            &nbsp;批量删除{{ selectedIds.length ? ` (${selectedIds.length})` : '' }}
          </el-button>
        </section>

        <section
          v-loading="loading"
          class="script-grid"
          element-loading-background="rgba(13, 17, 23, 0.55)"
        >
          <el-empty
            v-if="!loading && filteredScripts.length === 0"
            class="empty-state"
            description="该项目暂无剧本，点击右上角新建"
          />

          <article
            v-for="script in paginatedScripts"
            :key="script.id"
            class="script-card"
            :class="{ 'is-selected': selectedIds.includes(script.id) }"
            @click="openEditDialog(script)"
          >
            <header class="card-header">
              <h3 class="card-title" :title="script.name">{{ script.name }}</h3>
              <el-checkbox
                :model-value="selectedIds.includes(script.id)"
                class="card-checkbox"
                @click.stop
                @change="(value: unknown) => toggleSelect(script.id, !!value)"
              />
            </header>

            <p class="card-preview" :title="script.intro">{{ script.intro }}</p>

            <div class="card-assets">
              <span
                v-for="asset in script.relatedAssets"
                :key="asset.id"
                class="asset-chip"
                :class="`asset-chip--${asset.type}`"
                :title="asset.describe"
              >
                {{ asset.name }}
              </span>
              <span v-if="script.relatedAssets.length === 0" class="asset-empty">
                尚未提取资产
              </span>
            </div>

            <footer class="card-footer">
              <span
                class="status-chip"
                :class="statusClass(script.extractState)"
                :title="script.extractState === -1 && script.errorReason ? script.errorReason : ''"
              >
                <span class="status-dot"></span>
                {{ statusText(script.extractState) }}
              </span>
              <button
                class="card-delete-btn"
                aria-label="删除剧本"
                @click.stop="deleteScript(script)"
              >
                <el-icon><Delete /></el-icon>
              </button>
            </footer>
          </article>
        </section>

        <div v-if="filteredScripts.length > 0" class="pagination-wrap">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="filteredScripts.length"
            layout="prev, pager, next, total"
            background
          />
        </div>
      </section>
    </div>

    <Settings v-model="settingsVisible" />

    <el-dialog
      v-model="formDialogVisible"
      :title="formDialogTitle"
      width="min(1080px, calc(100vw - 32px))"
      destroy-on-close
      append-to-body
      class="script-dark-dialog"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        class="script-form"
        label-position="top"
      >
        <el-form-item label="剧本名称" prop="name">
          <el-input
            v-model="form.name"
            placeholder="如：青云 EP01：青云初入"
            maxlength="120"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="剧本正文" prop="content">
          <MarkdownEditor
            v-model="form.content"
            placeholder="支持 Markdown 语法，可粘贴完整分集剧本结构"
            height="520px"
          />
        </el-form-item>

        <el-form-item label="关联资产" prop="relatedAssetIds">
          <el-select
            v-model="form.relatedAssetIds"
            class="script-asset-select"
            multiple
            collapse-tags
            collapse-tags-tooltip
            filterable
            popper-class="script-dark-select"
            placeholder="选择关联的角色 / 场景 / 道具 / 镜头"
          >
            <el-option-group
              v-for="group in groupedAssetOptions"
              :key="group.type"
              :label="`${assetTypeLabel(group.type)}（${group.items.length}）`"
            >
              <el-option
                v-for="asset in group.items"
                :key="asset.id"
                :label="asset.name"
                :value="asset.id"
              >
                <div class="asset-option">
                  <span :class="`asset-option__type asset-option__type--${asset.type}`">
                    {{ assetTypeLabel(asset.type) }}
                  </span>
                  <span class="asset-option__name">{{ asset.name }}</span>
                  <span v-if="asset.describe" class="asset-option__desc">{{ asset.describe }}</span>
                </div>
              </el-option>
            </el-option-group>
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">
          保存
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="importDialogVisible"
      title="导入剧本"
      width="min(1180px, calc(100vw - 48px))"
      destroy-on-close
      append-to-body
      class="script-dark-dialog script-import-dialog"
      @close="resetImportState"
    >
      <el-steps :active="importStep - 1" finish-status="success" align-center class="import-steps">
        <el-step title="输入内容" />
        <el-step title="预览剧本" />
      </el-steps>

      <div v-show="importStep === 1" class="import-step">
        <el-radio-group v-model="importMode" class="import-mode">
          <el-radio-button value="bulk">按文件批量导入</el-radio-button>
          <el-radio-button value="split">单文件 / 粘贴 + 切分规则</el-radio-button>
        </el-radio-group>
        <p class="import-mode__hint">
          <span v-if="importMode === 'bulk'">每个上传的文件视为一份剧本，文件名作为剧本名</span>
          <span v-else>从单份文件或粘贴内容中按标题正则切分多份剧本</span>
        </p>

        <template v-if="importMode === 'bulk'">
          <el-upload
            class="import-uploader"
            drag
            multiple
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleBulkImportFile"
            accept=".txt,.md,.markdown,.docx,.pdf"
          >
            <el-icon class="import-uploader__icon"><UploadFilled /></el-icon>
            <div class="import-uploader__text">
              <strong>点击或拖拽多份剧本文件到此处</strong>
              <span>支持 .md / .txt（自动识别 UTF-8 / GBK） · .docx · .pdf，单文件 ≤ 10 MB</span>
            </div>
          </el-upload>

          <div v-if="bulkParsed.length > 0" class="import-bulk">
            <header class="import-bulk__head">
              <h4 class="import-bulk__title">已就绪的剧本</h4>
              <span class="import-bulk__count">共 {{ bulkParsed.length }} 份 · 拖拽调整顺序</span>
            </header>
            <ul class="import-bulk__list">
              <li
                v-for="(item, idx) in bulkParsed"
                :key="item.key"
                class="import-bulk__item"
                :class="{
                  'is-dragging': bulkDragIndex === idx,
                  'is-drop-before': bulkDropIndex === idx && bulkDropPosition === 'before',
                  'is-drop-after': bulkDropIndex === idx && bulkDropPosition === 'after',
                }"
                draggable="true"
                @dragstart="onBulkDragStart($event, idx)"
                @dragover.prevent="onBulkDragOver($event, idx)"
                @dragleave="onBulkDragLeave(idx)"
                @drop.prevent="onBulkDrop(idx)"
                @dragend="onBulkDragEnd"
              >
                <div class="import-bulk__main">
                  <span class="import-bulk__handle" aria-label="拖拽排序">
                    <el-icon><Rank /></el-icon>
                  </span>
                  <span class="import-bulk__seq">{{ idx + 1 }}</span>
                  <div class="import-bulk__info">
                    <span class="import-bulk__name" :title="item.name">{{ item.name }}</span>
                    <span class="import-bulk__meta">{{ item.detail }} · {{ item.content.length }} 字符</span>
                  </div>
                </div>
                <el-button link type="danger" size="small" @click="removeBulkItem(idx)">移除</el-button>
              </li>
            </ul>
          </div>
        </template>

        <template v-if="importMode === 'split'">
          <el-upload
            class="import-uploader"
            drag
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleSplitImportFile"
            accept=".txt,.md,.markdown,.docx,.pdf"
          >
            <el-icon class="import-uploader__icon"><UploadFilled /></el-icon>
            <div class="import-uploader__text">
              <strong>点击或拖拽单份文件到此处</strong>
              <span>支持 .md / .txt（自动识别 UTF-8 / GBK） · .docx · .pdf，单文件 ≤ 10 MB</span>
            </div>
            <div v-if="importFileName" class="import-uploader__file">
              已选择：{{ importFileName }}
            </div>
          </el-upload>

          <el-divider class="import-divider">或直接粘贴剧本内容</el-divider>

          <el-input
            v-model="importRaw"
            type="textarea"
            :rows="10"
            placeholder="粘贴剧本全文。系统按预设规则识别一级 / 二级标题、EP 编号、第 N 集等切分多份剧本。"
          />

          <div class="import-meta">
            <span>字符数：<strong>{{ importRaw.length }}</strong></span>
            <span>识别剧本：<strong>{{ splitParsed.length }}</strong></span>
            <span
              v-if="importRaw.length > 0 && splitParsed.length === 0"
              class="import-meta__warn"
            >未识别到剧本，请在下方调整切分规则</span>
          </div>

          <section class="import-split">
            <header class="import-split__head">
              <div>
                <h4 class="import-split__title">剧本切分规则</h4>
                <p class="import-split__hint">选择预设后可直接修改下方正则与匹配方式；上方"识别剧本"计数与下一步预览实时刷新。</p>
              </div>
            </header>

            <div class="import-split__main">
              <el-select
                v-model="splitPresetKey"
                class="import-split__select"
                popper-class="script-dark-select"
              >
                <el-option
                  v-for="preset in splitPresets"
                  :key="preset.key"
                  :label="preset.label"
                  :value="preset.key"
                >
                  <div class="import-split__opt">
                    <span class="import-split__opt-label">{{ preset.label }}</span>
                    <span class="import-split__opt-desc">{{ preset.description }}</span>
                  </div>
                </el-option>
              </el-select>

              <div class="import-split__editor">
                <div class="import-split__row">
                  <label class="import-split__row-label">剧本</label>
                  <el-input
                    v-model="currentSplitRule.titlePattern"
                    size="small"
                    placeholder="剧本标题正则（必填）"
                    class="import-split__row-pattern"
                  />
                  <el-select
                    v-model="currentSplitRule.titleFlagsList"
                    multiple
                    collapse-tags
                    collapse-tags-tooltip
                    size="small"
                    placeholder="匹配方式"
                    popper-class="script-dark-select"
                    class="import-split__row-flags"
                  >
                    <el-option
                      v-for="opt in FLAG_OPTIONS"
                      :key="opt.value"
                      :label="opt.label"
                      :value="opt.value"
                    />
                  </el-select>
                </div>
              </div>
            </div>
          </section>
        </template>
      </div>

      <div v-show="importStep === 2" class="import-step">
        <div class="import-preview__head">
          共识别 <strong>{{ importParsed.length }}</strong> 份剧本，已选
          <strong>{{ importSelectedRows.length }}</strong> 份入库
        </div>

        <el-table
          ref="importTableRef"
          :data="importParsed"
          class="script-import-table"
          height="420"
          row-key="key"
          :tooltip-options="{ effect: 'dark', popperClass: 'script-cell-tooltip' }"
          @selection-change="onImportSelectionChange"
        >
          <el-table-column type="selection" width="48" />
          <el-table-column label="#" type="index" width="60" />
          <el-table-column prop="name" label="剧本名称" min-width="280" show-overflow-tooltip />
          <el-table-column prop="detail" label="来源" width="180" show-overflow-tooltip />
          <el-table-column label="字数" width="100">
            <template #default="{ row }">
              <span class="row-count">{{ row.content.length }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="96" align="center">
            <template #default="{ row, $index }">
              <el-button
                link
                type="primary"
                class="row-edit-btn"
                @click="openPreviewEdit(row, $index)"
              >
                <el-icon><EditPen /></el-icon>
                <span>编辑</span>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <template #footer>
        <el-button v-if="importStep === 2" @click="importStep = 1">上一步</el-button>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button
          v-if="importStep === 1"
          type="primary"
          @click="goImportNext"
        >下一步</el-button>
        <el-button
          v-if="importStep === 2"
          type="primary"
          :loading="importSubmitting"
          :disabled="importSelectedRows.length === 0"
          @click="submitImport"
        >确认导入 ({{ importSelectedRows.length }})</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="previewEditVisible"
      title="编辑剧本"
      width="min(1080px, calc(100vw - 32px))"
      destroy-on-close
      append-to-body
      class="script-dark-dialog script-preview-edit-dialog"
    >
      <el-form
        :model="previewEditDraft"
        class="script-form"
        label-position="top"
      >
        <el-form-item label="剧本名称">
          <el-input
            v-model="previewEditDraft.name"
            placeholder="剧本名称"
            maxlength="120"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="剧本正文">
          <MarkdownEditor
            v-model="previewEditDraft.content"
            placeholder="支持 Markdown 语法，可粘贴完整分集剧本结构"
            height="520px"
          />
        </el-form-item>

        <div v-if="previewEditDraft.detail" class="preview-edit__meta">
          来源：{{ previewEditDraft.detail }} · 字数 {{ previewEditDraft.content.length }}
        </div>
      </el-form>

      <template #footer>
        <el-button @click="previewEditVisible = false">取消</el-button>
        <el-button type="primary" @click="savePreviewEdit">保存修改</el-button>
      </template>
    </el-dialog>
  </main>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import {
  CaretBottom,
  CaretTop,
  Connection,
  Delete,
  Document,
  Download,
  EditPen,
  Folder,
  List,
  MagicStick,
  Plus,
  Rank,
  Search,
  Select,
  Setting,
  Sort,
  Tickets,
  Upload,
  UploadFilled,
} from '@element-plus/icons-vue'
import Settings from '../components/Settings.vue'
import MarkdownEditor from '../components/MarkdownEditor.vue'

type ExtractState = -1 | 0 | 1 | 2
type AssetType = 'role' | 'prop' | 'scene' | 'shot'

interface ScriptAsset {
  id: number
  name: string
  describe: string
  type: AssetType
}

interface ScriptRecord {
  id: number
  projectId: number
  name: string
  intro: string
  content: string
  extractState: ExtractState
  errorReason: string | null
  relatedAssets: ScriptAsset[]
  createdAt: string
}

const router = useRouter()

const scripts = ref<ScriptRecord[]>([
  {
    id: 1,
    projectId: 1,
    name: '青云 EP01：青云初入',
    intro:
      '# 青云 EP01：青云初入 # 目标时长：24分钟 ≈ 3600字小说 # 平台：横屏 16:9 | 风格：3D_chinese_traditional | 背景：山野开场-仙门奇缘-异人现身-归途埋雷',
    content:
      '# 青云 EP01：青云初入\n\n# 目标时长：24分钟 ≈ 3600字小说\n# 平台：横屏 16:9 | 风格：3D_chinese_traditional\n# 背景：山野开场-仙门奇缘-异人现身-归途埋雷\n\n---\n\n## 剧情梗概\n\n青云山下草庙村清晨，一处濒临塌顶的破庙，两个孩子追闹时险些误伤路人性命，破庙中一位衣衫褴褛的老和尚突然现身，以一串可思议的手段制止了冲突。张小凡与林惊羽第一次直面"神迹"，也第一次意识到，自己生活的小村头顶那座青云山之间，并不只是百姓本份。',
    extractState: 2,
    errorReason: null,
    relatedAssets: [
      { id: 101, name: '张小凡', describe: '草庙村少年，主角', type: 'role' },
      { id: 102, name: '林惊羽', describe: '草庙村少年，张小凡好友', type: 'role' },
      { id: 103, name: '老和尚', describe: '破庙中现身的神秘异人', type: 'role' },
      { id: 104, name: '王二叔', describe: '草庙村村民', type: 'role' },
      { id: 105, name: '张父', describe: '张小凡之父，木匠', type: 'role' },
      { id: 106, name: '张母', describe: '张小凡之母', type: 'role' },
      { id: 107, name: '林父', describe: '林惊羽之父，猎户', type: 'role' },
      { id: 108, name: '林母', describe: '林惊羽之母', type: 'role' },
      { id: 109, name: '青衣道人', describe: '远景出现的青云门修士', type: 'role' },
      { id: 110, name: '草庙村外荒坡', describe: '剧情开场山野场景', type: 'scene' },
      { id: 111, name: '草庙内', describe: '破败的草庙内景', type: 'scene' },
      { id: 112, name: '草庙村村道', describe: '黄昏的村庄主路', type: 'scene' },
      { id: 113, name: '张家院子', describe: '张家土院与厨房', type: 'scene' },
      { id: 114, name: '林家院外', describe: '林家篱笆与晾架', type: 'scene' },
      { id: 115, name: '张小凡房间', describe: '土炕与油灯', type: 'scene' },
      { id: 116, name: '青云山远景', describe: '云海中的青云山主峰', type: 'scene' },
      { id: 117, name: '碧玉念珠', describe: '老和尚手中的念珠', type: 'prop' },
      { id: 118, name: '削尖的木棍', describe: '少年随手取作武器', type: 'prop' },
      { id: 119, name: '飞剑', describe: '青云道人脚下飞剑', type: 'prop' },
      { id: 120, name: '砍柴小斧', describe: '村中常见劳具', type: 'prop' },
      { id: 121, name: '猎弓和风干兽皮', describe: '林家陈设', type: 'prop' },
      { id: 122, name: '村服', describe: '少年常服', type: 'prop' },
      { id: 123, name: '旧麻鞋', describe: '草庙村常见鞋履', type: 'prop' },
      { id: 124, name: '柴夫装', describe: '柴夫角色服饰', type: 'prop' },
      { id: 125, name: '农夫装', describe: '村中男性常服', type: 'prop' },
      { id: 126, name: '农妇装', describe: '村中女性常服', type: 'prop' },
      { id: 127, name: '猎户装', describe: '林父出场服饰', type: 'prop' },
      { id: 128, name: '村妇装', describe: '村中女性配饰', type: 'prop' },
      { id: 129, name: '道袍态', describe: '青云门道袍款式', type: 'prop' },
      { id: 130, name: '夜庙', describe: '老和尚独坐破庙的夜景镜头', type: 'shot' },
      { id: 131, name: '夜灵山', describe: '远景青云山入夜镜头', type: 'shot' },
      { id: 132, name: '青光态', describe: '飞剑划破天际的特写', type: 'shot' },
      { id: 133, name: '群童追逐态', describe: '少年追逐打闹镜头', type: 'shot' },
      { id: 134, name: '孩童围观态', describe: '孩童围观惊讶反应', type: 'shot' },
      { id: 135, name: '村民围拢态', describe: '村民围观议论镜头', type: 'shot' },
    ],
    createdAt: '2026-05-18 09:32',
  },
  {
    id: 2,
    projectId: 1,
    name: '青云 EP02：意外坠入古窟',
    intro:
      '# 青云 EP02：意外坠入古窟 # 目标时长：24分钟 ≈ 3600字小说 # 平台：横屏 16:9 | 风格：3D_chinese_traditional | 背景：荒原追逐-地裂塌陷-古窟探幽-异色光匣',
    content:
      '# 青云 EP02：意外坠入古窟\n\n# 目标时长：24分钟 ≈ 3600字小说\n# 平台：横屏 16:9 | 风格：3D_chinese_traditional\n# 背景：荒原追逐-地裂塌陷-古窟探幽-异色光匣\n\n---\n\n## 剧情梗概\n\n张小凡与林惊羽追入山外荒坡，足下地砖崩塌，二人跌入沉睡千年的古窟。窟中残殿幽冷，断龛之上一只青色光匣自鸣自亮，匣中似有低声呼应。一道黑影自暗处出现，对二人多有试探，又在听到老和尚的名讳后退避而走。',
    extractState: 2,
    errorReason: null,
    relatedAssets: [
      { id: 201, name: '张小凡', describe: '主角', type: 'role' },
      { id: 202, name: '林惊羽', describe: '张小凡好友', type: 'role' },
      { id: 203, name: '老和尚', describe: '远景出现于回忆', type: 'role' },
      { id: 204, name: '张父', describe: '出场于回忆', type: 'role' },
      { id: 205, name: '张母', describe: '出场于回忆', type: 'role' },
      { id: 206, name: '林父', describe: '出场于回忆', type: 'role' },
      { id: 207, name: '林母', describe: '出场于回忆', type: 'role' },
      { id: 208, name: '神秘黑衣人', describe: '古窟中现身的异修', type: 'role' },
      { id: 209, name: '草庙内', describe: '过场场景', type: 'scene' },
      { id: 210, name: '林家院外', describe: '过场场景', type: 'scene' },
      { id: 211, name: '张小凡房间', describe: '过场场景', type: 'scene' },
      { id: 212, name: '古窟残殿', describe: '坠落后的核心场景', type: 'scene' },
      { id: 213, name: '佛珠', describe: '与老和尚念珠呼应的法器', type: 'prop' },
      { id: 214, name: '碧玉念珠', describe: '青色光匣的关联物', type: 'prop' },
    ],
    createdAt: '2026-05-18 10:08',
  },
  {
    id: 3,
    projectId: 1,
    name: '青云 EP03：伤痛与妖逝',
    intro:
      '# 青云 EP03：伤痛与妖逝 # 目标时长：24分钟 ≈ 3600字小说 # 平台：横屏 16:9 | 风格：3D_chinese_traditional | 背景：噩耗归村-旧伤复发-黑影再现-念珠化光',
    content:
      '# 青云 EP03：伤痛与妖逝\n\n# 目标时长：24分钟 ≈ 3600字小说\n# 平台：横屏 16:9 | 风格：3D_chinese_traditional\n# 背景：噩耗归村-旧伤复发-黑影再现-念珠化光\n\n---\n\n## 剧情梗概\n\n二人狼狈回村，却撞见村口的灯笼断了一节。张家与林家相继传出噩耗，张小凡胸口旧伤再次发作，碧玉念珠在掌心透出微光。那道黑影循着光气追至草庙村外，终被一位远来的青云门修士斩去半身，残魂化为青烟消散。',
    extractState: 2,
    errorReason: null,
    relatedAssets: [
      { id: 301, name: '张小凡', describe: '主角', type: 'role' },
      { id: 302, name: '林惊羽', describe: '同伴', type: 'role' },
      { id: 303, name: '老和尚', describe: '念珠所留之人', type: 'role' },
      { id: 304, name: '张父', describe: '本集去世', type: 'role' },
      { id: 305, name: '张母', describe: '本集去世', type: 'role' },
      { id: 306, name: '林父', describe: '本集去世', type: 'role' },
      { id: 307, name: '林母', describe: '本集去世', type: 'role' },
      { id: 308, name: '神秘黑衣人', describe: '最终被斩', type: 'role' },
      { id: 309, name: '青衣道人', describe: '出手斩妖的青云门修士', type: 'role' },
      { id: 310, name: '张家院子', describe: '剧情核心场景', type: 'scene' },
      { id: 311, name: '草庙地穴出口', describe: '黑影再现场景', type: 'scene' },
      { id: 312, name: '古窟残殿', describe: '回闪场景', type: 'scene' },
      { id: 313, name: '佛珠', describe: '念珠化光主道具', type: 'prop' },
      { id: 314, name: '碧玉念珠', describe: '本集核心法器', type: 'prop' },
      { id: 315, name: '夜雨态', describe: '雨夜悲鸣的氛围镜头', type: 'shot' },
    ],
    createdAt: '2026-05-18 11:15',
  },
  {
    id: 4,
    projectId: 1,
    name: '青云 EP04：隐忧重返青云',
    intro:
      '# 青云 EP04：隐忧重返青云 # 目标时长：24分钟 ≈ 3600字小说 # 平台：横屏 16:9 | 风格：3D_chinese_traditional | 背景：携孤上山-入门考较-初见三代-暗藏隐忧',
    content:
      '# 青云 EP04：隐忧重返青云\n\n# 目标时长：24分钟 ≈ 3600字小说\n# 平台：横屏 16:9 | 风格：3D_chinese_traditional\n# 背景：携孤上山-入门考较-初见三代-暗藏隐忧\n\n---\n\n## 剧情梗概\n\n青衣道人将张小凡与林惊羽带回青云山，七脉首座云海之上议事。大竹峰首座田不易性情倔强，对张小凡口齿木讷颇为不满；苏茹温言相劝，田灵儿在一旁好奇打量。看似平稳入门的少年，胸口仍残留着古窟那点不可解的紫光。',
    extractState: 2,
    errorReason: null,
    relatedAssets: [
      { id: 401, name: '张小凡', describe: '主角，入大竹峰', type: 'role' },
      { id: 402, name: '林惊羽', describe: '同期入门，资质拔尖', type: 'role' },
      { id: 403, name: '田不易', describe: '大竹峰首座', type: 'role' },
      { id: 404, name: '宋大仁', describe: '大竹峰大弟子', type: 'role' },
      { id: 405, name: '苏茹', describe: '田不易之妻', type: 'role' },
      { id: 406, name: '田灵儿', describe: '田不易爱女', type: 'role' },
      { id: 407, name: '青云山云海上', describe: '七脉议事场景', type: 'scene' },
      { id: 408, name: '大竹峰前山广坪', describe: '入门考较场景', type: 'scene' },
      { id: 409, name: '佛珠', describe: '主角贴身法器', type: 'prop' },
      { id: 410, name: '剑', describe: '青云门弟子佩剑', type: 'prop' },
      { id: 411, name: '云上俯瞰态', describe: '广坪入门远镜头', type: 'shot' },
    ],
    createdAt: '2026-05-19 08:42',
  },
  {
    id: 5,
    projectId: 1,
    name: '青云 EP05：十年之后',
    intro:
      '# 青云 EP05：十年之后 # 目标时长：24分钟 ≈ 3600字小说 # 平台：横屏 16:9 | 风格：3D_chinese_traditional | 背景：十年磨炼-性情转折-鬼王初谋-旧念暗发',
    content:
      '# 青云 EP05：十年之后\n\n# 目标时长：24分钟 ≈ 3600字小说\n# 平台：横屏 16:9 | 风格：3D_chinese_traditional\n# 背景：十年磨炼-性情转折-鬼王初谋-旧念暗发\n\n---\n\n## 剧情梗概\n\n十年过去，张小凡在大竹峰默默砍柴打杂，胸口紫光偶有闪烁。鬼王宗中一位名为周一仙的怪人借小环之口探听少年消息，噬魂棒与黑心令在阴山之畔同时发动……风暴尚未到来，平静的山门内已有暗流涌动。',
    extractState: 0,
    errorReason: null,
    relatedAssets: [],
    createdAt: '2026-05-19 14:25',
  },
])
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(6)
const loading = ref(false)
const extracting = ref(false)

const selectedIds = ref<number[]>([])
const settingsVisible = ref(false)

const formDialogVisible = ref(false)
const formMode = ref<'create' | 'edit'>('create')
const editingId = ref<number | null>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  content: '',
  relatedAssetIds: [] as number[],
})

const formRules: FormRules<typeof form> = {
  name: [
    { required: true, message: '请输入剧本名称', trigger: 'blur' },
    { max: 120, message: '剧本名称不超过 120 个字符', trigger: 'blur' },
  ],
  content: [{ required: true, message: '请输入剧本正文', trigger: 'blur' }],
}

const formDialogTitle = computed(() => (formMode.value === 'create' ? '新建剧本' : '编辑剧本'))

const resetForm = () => {
  form.name = ''
  form.content = ''
  form.relatedAssetIds = []
  formRef.value?.clearValidate()
}

const extractIntroFromContent = (content: string): string => {
  const headerLines: string[] = []
  for (const rawLine of content.split('\n')) {
    const line = rawLine.trim()
    if (!line) {
      if (headerLines.length > 0) break
      continue
    }
    if (line.startsWith('---')) break
    if (line.startsWith('#')) headerLines.push(line)
    else if (headerLines.length === 0) headerLines.push(line)
    else break
    if (headerLines.length >= 4) break
  }
  return headerLines.join(' ').slice(0, 500)
}

const ASSET_TYPE_LABELS: Record<AssetType, string> = {
  role: '角色',
  scene: '场景',
  prop: '道具',
  shot: '镜头',
}

const ASSET_TYPE_ORDER: AssetType[] = ['role', 'scene', 'prop', 'shot']

const assetTypeLabel = (type: AssetType) => ASSET_TYPE_LABELS[type]

const assetOptions = computed<ScriptAsset[]>(() => {
  const map = new Map<number, ScriptAsset>()
  scripts.value.forEach((script) => {
    script.relatedAssets.forEach((asset) => {
      if (!map.has(asset.id)) map.set(asset.id, asset)
    })
  })
  return Array.from(map.values()).sort((a, b) => {
    if (a.type !== b.type) {
      return ASSET_TYPE_ORDER.indexOf(a.type) - ASSET_TYPE_ORDER.indexOf(b.type)
    }
    return a.name.localeCompare(b.name, 'zh-CN')
  })
})

const groupedAssetOptions = computed<{ type: AssetType; items: ScriptAsset[] }[]>(() => {
  const groups: { type: AssetType; items: ScriptAsset[] }[] = []
  ASSET_TYPE_ORDER.forEach((type) => {
    const items = assetOptions.value.filter((asset) => asset.type === type)
    if (items.length > 0) groups.push({ type, items })
  })
  return groups
})

type SortField = 'id' | 'createdAt' | 'name' | 'extractState' | 'assetCount'
type SortOrder = 'asc' | 'desc'

const SORT_OPTIONS: { value: SortField; label: string }[] = [
  { value: 'id', label: '剧本编号' },
  { value: 'createdAt', label: '创建时间' },
  { value: 'name', label: '剧本名称' },
  { value: 'extractState', label: '提取状态' },
  { value: 'assetCount', label: '资产数量' },
]

const sortField = ref<SortField>('createdAt')
const sortOrder = ref<SortOrder>('desc')

const currentSortLabel = computed(
  () => SORT_OPTIONS.find((opt) => opt.value === sortField.value)?.label ?? '创建时间',
)

const onSortCommand = (cmd: SortField) => {
  if (sortField.value === cmd) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = cmd
    sortOrder.value = 'desc'
  }
  currentPage.value = 1
}

const filteredScripts = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase()
  const dir = sortOrder.value === 'asc' ? 1 : -1
  return scripts.value
    .filter((item) => (keyword ? item.name.toLowerCase().includes(keyword) : true))
    .sort((a, b) => {
      switch (sortField.value) {
        case 'id':
          return (a.id - b.id) * dir
        case 'name':
          return a.name.localeCompare(b.name, 'zh-CN') * dir
        case 'extractState':
          return (a.extractState - b.extractState) * dir
        case 'assetCount':
          return (a.relatedAssets.length - b.relatedAssets.length) * dir
        case 'createdAt':
        default:
          return a.createdAt.localeCompare(b.createdAt) * dir
      }
    })
})

const paginatedScripts = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredScripts.value.slice(start, start + pageSize.value)
})

const isAllSelected = computed(
  () => filteredScripts.value.length > 0 && selectedIds.value.length === filteredScripts.value.length,
)

const STATUS_LABELS: Record<ExtractState, string> = {
  [-1]: '提取失败',
  0: '待提取',
  1: '提取中',
  2: '已提取',
}

const STATUS_CLASS: Record<ExtractState, string> = {
  [-1]: 'is-failed',
  0: 'is-pending',
  1: 'is-extracting',
  2: 'is-completed',
}

const statusText = (state: ExtractState) => STATUS_LABELS[state]
const statusClass = (state: ExtractState) => STATUS_CLASS[state]

const toggleSelect = (id: number, checked: boolean) => {
  if (checked) {
    if (!selectedIds.value.includes(id)) {
      selectedIds.value = [...selectedIds.value, id]
    }
  } else {
    selectedIds.value = selectedIds.value.filter((sid) => sid !== id)
  }
}

const openEditDialog = (script: ScriptRecord) => {
  formMode.value = 'edit'
  editingId.value = script.id
  form.name = script.name
  form.content = script.content
  form.relatedAssetIds = script.relatedAssets.map((asset) => asset.id)
  formDialogVisible.value = true
  formRef.value?.clearValidate()
}

const deleteScript = async (script: ScriptRecord) => {
  try {
    await ElMessageBox.confirm(
      `确定删除「${script.name}」吗？删除后不可恢复。`,
      '删除剧本',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
        customClass: 'script-dark-messagebox',
      },
    )
    scripts.value = scripts.value.filter((item) => item.id !== script.id)
    selectedIds.value = selectedIds.value.filter((sid) => sid !== script.id)
    ElMessage.success('剧本已删除')
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error('删除失败')
  }
}

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = filteredScripts.value.map((item) => item.id)
  }
}

const openCreateDialog = () => {
  formMode.value = 'create'
  editingId.value = null
  resetForm()
  formDialogVisible.value = true
}

const submitForm = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  await new Promise((resolve) => setTimeout(resolve, 200))

  try {
    const intro = extractIntroFromContent(form.content)
    const selectedAssets = form.relatedAssetIds
      .map((id) => assetOptions.value.find((asset) => asset.id === id))
      .filter((asset): asset is ScriptAsset => Boolean(asset))

    if (formMode.value === 'create') {
      const newId = scripts.value.reduce((max, item) => Math.max(max, item.id), 0) + 1
      const now = new Date()
      const pad = (n: number) => String(n).padStart(2, '0')
      const createdAt = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`

      scripts.value.push({
        id: newId,
        projectId: 1,
        name: form.name.trim(),
        intro,
        content: form.content,
        extractState: selectedAssets.length > 0 ? 2 : 0,
        errorReason: null,
        relatedAssets: selectedAssets,
        createdAt,
      })
      ElMessage.success('剧本已新建')
    } else if (editingId.value !== null) {
      const target = scripts.value.find((item) => item.id === editingId.value)
      if (target) {
        target.name = form.name.trim()
        target.intro = intro
        target.content = form.content
        target.relatedAssets = selectedAssets
        if (selectedAssets.length > 0 && target.extractState === 0) {
          target.extractState = 2
        }
        ElMessage.success('剧本已更新')
      }
    }

    formDialogVisible.value = false
  } finally {
    submitting.value = false
  }
}

const openBatchImportDialog = () => {
  resetImportState()
  importDialogVisible.value = true
}

const batchExtractAssets = () => {
  ElMessage.info('功能开发中')
}

const batchExportZip = () => {
  ElMessage.info('功能开发中')
}

const batchDeleteSelected = () => {
  ElMessage.info('功能开发中')
}

interface ImportScriptDraft {
  key: number
  name: string
  detail: string
  content: string
}

const importDialogVisible = ref(false)
const importStep = ref<1 | 2>(1)
const importMode = ref<'bulk' | 'split'>('bulk')

const importRaw = ref('')
const importFileName = ref('')
const bulkParsed = ref<ImportScriptDraft[]>([])
const importTableRef = ref()
const importSelectedRows = ref<ImportScriptDraft[]>([])
const importSubmitting = ref(false)

const bulkDragIndex = ref<number | null>(null)
const bulkDropIndex = ref<number | null>(null)
const bulkDropPosition = ref<'before' | 'after' | null>(null)

const onBulkDragStart = (event: DragEvent, index: number) => {
  bulkDragIndex.value = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(index))
  }
}

const onBulkDragOver = (event: DragEvent, index: number) => {
  if (bulkDragIndex.value === null) return
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'move'
  const target = event.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const offset = event.clientY - rect.top
  bulkDropIndex.value = index
  bulkDropPosition.value = offset < rect.height / 2 ? 'before' : 'after'
}

const onBulkDragLeave = (index: number) => {
  if (bulkDropIndex.value === index) {
    bulkDropIndex.value = null
    bulkDropPosition.value = null
  }
}

const onBulkDrop = (index: number) => {
  const from = bulkDragIndex.value
  const position = bulkDropPosition.value
  bulkDragIndex.value = null
  bulkDropIndex.value = null
  bulkDropPosition.value = null
  if (from === null || from === index) return
  let to = index + (position === 'after' ? 1 : 0)
  if (from < to) to -= 1
  if (to === from) return
  const list = bulkParsed.value.slice()
  const [moved] = list.splice(from, 1)
  list.splice(to, 0, moved)
  bulkParsed.value = list
}

const onBulkDragEnd = () => {
  bulkDragIndex.value = null
  bulkDropIndex.value = null
  bulkDropPosition.value = null
}

interface ImportSplitPreset {
  key: string
  label: string
  description: string
  titlePattern: string
  titleFlagsList: string[]
}

const splitPresets = ref<ImportSplitPreset[]>([
  {
    key: 'md-h1',
    label: '一级标题（# ）',
    description: '识别 Markdown 一级标题作为剧本名，逐份切分',
    titlePattern: '^\\s*#\\s+[^\\n\\r]+$',
    titleFlagsList: ['m'],
  },
  {
    key: 'md-h2',
    label: '二级标题（## ）',
    description: '识别 Markdown 二级标题，常用于「## 第 01 集」',
    titlePattern: '^\\s*##\\s+[^\\n\\r]+$',
    titleFlagsList: ['m'],
  },
  {
    key: 'ep',
    label: 'EP 编号（EP01 / EP 1）',
    description: '识别 EP + 数字开头的标题行',
    titlePattern: '^\.\*\?EP\\s*\\d+\.\*?$',
    titleFlagsList: ['i', 'm'],
  },
  {
    key: 'cn-ep',
    label: '第 X 集',
    description: '识别「第一集 / 第 01 集 / 第 N 集」',
    titlePattern: '^\\s*第\\s*[0-9一二三四五六七八九十百千零〇两]+\\s*集[^\\n\\r]*$',
    titleFlagsList: ['m'],
  },
  {
    key: 'custom',
    label: '自定义正则',
    description: '手动指定剧本标题的匹配正则',
    titlePattern: '',
    titleFlagsList: ['m'],
  },
])

const splitPresetKey = ref<string>('md-h1')

const currentSplitRule = computed<ImportSplitPreset>(
  () =>
    splitPresets.value.find((p) => p.key === splitPresetKey.value) ||
    splitPresets.value[0],
)

const parseScriptText = (
  raw: string,
  rule: ImportSplitPreset,
): ImportScriptDraft[] => {
  if (!raw || !rule.titlePattern) return []
  const flags = rule.titleFlagsList.includes('m')
    ? rule.titleFlagsList.join('')
    : `${rule.titleFlagsList.join('')}m`
  let titleRegex: RegExp
  try {
    titleRegex = new RegExp(rule.titlePattern, flags)
  } catch {
    return []
  }
  const lines = raw.split(/\r?\n/)
  const drafts: ImportScriptDraft[] = []
  let currentTitle = ''
  let currentBody: string[] = []

  const lineRegex = (() => {
    const lineFlags = rule.titleFlagsList.filter((f) => f !== 'm').join('')
    try {
      return new RegExp(rule.titlePattern, lineFlags)
    } catch {
      return null
    }
  })()
  if (!lineRegex) return []

  const flush = () => {
    if (currentTitle) {
      const name = currentTitle.replace(/^\s*#+\s*/, '').trim() || currentTitle.trim()
      drafts.push({
        key: drafts.length + 1,
        name,
        detail: '文本切分',
        content: [currentTitle, ...currentBody].join('\n').trim(),
      })
    }
    currentBody = []
  }

  for (const line of lines) {
    if (lineRegex.test(line)) {
      flush()
      currentTitle = line
    } else if (currentTitle) {
      currentBody.push(line)
    }
  }
  flush()
  // 确保至少匹配过：若 titleRegex 全文未命中，drafts 为空
  if (drafts.length === 0 && !titleRegex.test(raw)) return []
  return drafts
}

const splitParsed = computed(() =>
  parseScriptText(importRaw.value, currentSplitRule.value),
)

const importParsed = ref<ImportScriptDraft[]>([])

const snapshotImportParsed = () => {
  const source = importMode.value === 'bulk' ? bulkParsed.value : splitParsed.value
  importParsed.value = source.map((item) => ({ ...item }))
}

const previewEditVisible = ref(false)
const previewEditIndex = ref<number>(-1)
const previewEditDraft = reactive({ name: '', content: '', detail: '' })

const openPreviewEdit = (row: ImportScriptDraft, index: number) => {
  previewEditIndex.value = index
  previewEditDraft.name = row.name
  previewEditDraft.content = row.content
  previewEditDraft.detail = row.detail
  previewEditVisible.value = true
}

const savePreviewEdit = () => {
  if (previewEditIndex.value < 0) return
  const trimmedName = previewEditDraft.name.trim()
  if (!trimmedName) {
    ElMessage.warning('剧本名称不能为空')
    return
  }
  const target = importParsed.value[previewEditIndex.value]
  if (!target) {
    previewEditVisible.value = false
    return
  }
  const wasSelected = importSelectedRows.value.some((row) => row.key === target.key)
  const updated: ImportScriptDraft = {
    ...target,
    name: trimmedName,
    content: previewEditDraft.content,
  }
  importParsed.value.splice(previewEditIndex.value, 1, updated)
  previewEditVisible.value = false
  if (wasSelected) {
    nextTick(() => {
      importTableRef.value?.toggleRowSelection?.(updated, true)
    })
  }
  ElMessage.success('已更新该集剧本')
}

const FLAG_OPTIONS = [
  { value: 'g', label: '全局匹配（所有出现处都替换）' },
  { value: 'i', label: '忽略大小写' },
  { value: 'm', label: '多行模式（^ $ 匹配每一行）' },
  { value: 's', label: '点号匹配换行' },
]

const detectEncoding = (buffer: ArrayBuffer): 'utf-8' | 'gbk' => {
  const bytes = new Uint8Array(buffer)
  if (bytes.length >= 3 && bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf) {
    return 'utf-8'
  }
  if (
    bytes.length >= 2 &&
    ((bytes[0] === 0xff && bytes[1] === 0xfe) ||
      (bytes[0] === 0xfe && bytes[1] === 0xff))
  ) {
    return 'utf-8'
  }
  try {
    new TextDecoder('utf-8', { fatal: true }).decode(buffer)
    return 'utf-8'
  } catch {
    return 'gbk'
  }
}

const readFileAsArrayBuffer = (file: File): Promise<ArrayBuffer> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const buffer = e.target?.result as ArrayBuffer | null
      if (!buffer) reject(new Error('文件内容为空'))
      else resolve(buffer)
    }
    reader.onerror = () => reject(new Error('文件读取失败'))
    reader.readAsArrayBuffer(file)
  })

const extractTextFromTxt = async (
  buffer: ArrayBuffer,
): Promise<{ text: string; detail: string }> => {
  const encoding = detectEncoding(buffer)
  const decoder = new TextDecoder(encoding)
  return { text: decoder.decode(buffer), detail: `${encoding.toUpperCase()} 编码` }
}

const extractTextFromDocx = async (
  buffer: ArrayBuffer,
): Promise<{ text: string; detail: string }> => {
  const mammoth = await import('mammoth/mammoth.browser')
  const result = await mammoth.extractRawText({ arrayBuffer: buffer })
  return { text: result.value || '', detail: 'DOCX 文档' }
}

const extractTextFromPdf = async (
  buffer: ArrayBuffer,
): Promise<{ text: string; detail: string }> => {
  const pdfjsLib: any = await import('pdfjs-dist')
  const workerModule = await import('pdfjs-dist/build/pdf.worker.min.mjs?url')
  pdfjsLib.GlobalWorkerOptions.workerSrc = workerModule.default
  const loadingTask = pdfjsLib.getDocument({ data: new Uint8Array(buffer) })
  const pdf = await loadingTask.promise
  const pages: string[] = []
  for (let i = 1; i <= pdf.numPages; i += 1) {
    const page = await pdf.getPage(i)
    const content = await page.getTextContent()
    const lines: string[] = []
    let currentLine = ''
    let lastY: number | null = null
    for (const item of content.items as Array<{
      str: string
      transform?: number[]
      hasEOL?: boolean
    }>) {
      const y = item.transform?.[5] ?? null
      if (lastY !== null && y !== null && Math.abs(y - lastY) > 2) {
        if (currentLine.trim()) lines.push(currentLine.trim())
        currentLine = ''
      }
      currentLine += item.str
      if (item.hasEOL) {
        if (currentLine.trim()) lines.push(currentLine.trim())
        currentLine = ''
      }
      lastY = y
    }
    if (currentLine.trim()) lines.push(currentLine.trim())
    pages.push(lines.join('\n'))
  }
  return { text: pages.join('\n\n'), detail: `PDF ${pdf.numPages} 页` }
}

const validateImportFile = (file: File): boolean => {
  if (/\.doc$/i.test(file.name)) {
    ElMessage.error('暂不支持旧版 .doc（二进制 Word 97-2003），请另存为 .docx 后再上传')
    return false
  }
  if (!/\.(txt|md|markdown|docx|pdf)$/i.test(file.name)) {
    ElMessage.error('仅支持 .md / .txt / .docx / .pdf')
    return false
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error(`「${file.name}」超过 10 MB 限制`)
    return false
  }
  return true
}

const extractFileText = async (
  file: File,
): Promise<{ text: string; detail: string }> => {
  const buffer = await readFileAsArrayBuffer(file)
  if (/\.docx$/i.test(file.name)) return extractTextFromDocx(buffer)
  if (/\.pdf$/i.test(file.name)) return extractTextFromPdf(buffer)
  return extractTextFromTxt(buffer)
}

const fileNameToScriptName = (fname: string) =>
  fname.replace(/\.[^.]+$/, '').trim() || fname

const handleSplitImportFile = async (uploadFile: { raw?: File; name: string }) => {
  const rawFile = uploadFile?.raw
  if (!rawFile) {
    ElMessage.error('文件读取失败，请重新选择')
    return
  }
  if (!validateImportFile(rawFile)) return
  const loading = ElMessage({
    message: `正在解析 ${rawFile.name}…`,
    duration: 0,
    type: 'info',
  })
  try {
    const result = await extractFileText(rawFile)
    importRaw.value = result.text
    importFileName.value = rawFile.name
    ElMessage.success(
      `已读取 ${rawFile.name}（${result.detail}），共 ${importRaw.value.length} 字符`,
    )
  } catch (err) {
    ElMessage.error(`解析失败：${(err as Error).message}`)
  } finally {
    loading.close()
  }
}

let bulkSeq = 0
const handleBulkImportFile = async (uploadFile: { raw?: File; name: string }) => {
  const rawFile = uploadFile?.raw
  if (!rawFile) {
    ElMessage.error('文件读取失败，请重新选择')
    return
  }
  if (!validateImportFile(rawFile)) return
  const loading = ElMessage({
    message: `正在解析 ${rawFile.name}…`,
    duration: 0,
    type: 'info',
  })
  try {
    const result = await extractFileText(rawFile)
    const name = fileNameToScriptName(rawFile.name)
    if (!result.text.trim()) {
      ElMessage.warning(`「${rawFile.name}」未读取到文本内容，已跳过`)
      return
    }
    bulkSeq += 1
    bulkParsed.value.push({
      key: bulkSeq,
      name,
      detail: `${rawFile.name} · ${result.detail}`,
      content: result.text.trim(),
    })
    ElMessage.success(`已就绪：${name}（${result.text.length} 字符）`)
  } catch (err) {
    ElMessage.error(`解析失败：${(err as Error).message}`)
  } finally {
    loading.close()
  }
}

const removeBulkItem = (idx: number) => {
  bulkParsed.value.splice(idx, 1)
}

const onImportSelectionChange = (rows: ImportScriptDraft[]) => {
  importSelectedRows.value = rows
}

const goImportNext = () => {
  if (importMode.value === 'bulk') {
    if (bulkParsed.value.length === 0) {
      ElMessage.warning('请先上传至少一份剧本文件')
      return
    }
  } else {
    if (!importRaw.value.trim()) {
      ElMessage.warning('请先上传文件或粘贴剧本全文')
      return
    }
    if (splitParsed.value.length === 0) {
      ElMessage.warning('未识别到剧本，请检查切分规则')
      return
    }
  }
  importStep.value = 2
  snapshotImportParsed()
  nextTick(() => {
    importTableRef.value?.toggleAllSelection?.()
  })
}

const submitImport = async () => {
  if (importSelectedRows.value.length === 0) {
    ElMessage.warning('请至少选择一份剧本')
    return
  }
  importSubmitting.value = true
  await new Promise((resolve) => setTimeout(resolve, 200))

  let nextId = scripts.value.reduce((max, item) => Math.max(max, item.id), 0) + 1
  const now = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  const createdAt = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`

  for (const draft of importSelectedRows.value) {
    scripts.value.push({
      id: nextId++,
      projectId: 1,
      name: draft.name,
      intro: extractIntroFromContent(draft.content),
      content: draft.content,
      extractState: 0,
      errorReason: null,
      relatedAssets: [],
      createdAt,
    })
  }

  ElMessage.success(`已导入 ${importSelectedRows.value.length} 份剧本`)
  importDialogVisible.value = false
  importSubmitting.value = false
}

const resetImportState = () => {
  importStep.value = 1
  importMode.value = 'bulk'
  importRaw.value = ''
  importFileName.value = ''
  bulkParsed.value = []
  importParsed.value = []
  importSelectedRows.value = []
  importSubmitting.value = false
  splitPresetKey.value = 'md-h1'
}

const goProject = () => {
  router.push('/project')
}

const showComingSoon = () => {
  ElMessage.info('功能开发中')
}
</script>

<style scoped>
.script-page {
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

.sort-trigger {
  font-variant-numeric: tabular-nums;
}

.sort-trigger :deep(.el-icon) {
  font-size: 14px;
}

.sort-direction-icon {
  margin-left: 4px;
  font-size: 12px !important;
  opacity: 0.85;
}

.script-grid {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px 18px;
  align-content: start;
  padding-right: 6px;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.14) transparent;
}

.script-grid::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.script-grid::-webkit-scrollbar-track {
  background: transparent;
}

.script-grid::-webkit-scrollbar-thumb {
  background-color: rgba(255, 255, 255, 0.12);
  border-radius: 999px;
  transition: background-color 0.18s ease;
}

.script-grid::-webkit-scrollbar-thumb:hover {
  background-color: rgba(255, 255, 255, 0.24);
}

.empty-state {
  grid-column: 1 / -1;
  align-self: center;
  justify-self: center;
  padding: 60px 0;
}

.empty-state :deep(.el-empty__description p) {
  color: #6e7681;
  font-size: 13px;
}

.script-card {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 16px 16px 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.035), rgba(255, 255, 255, 0.014));
  box-shadow: 0 14px 36px rgba(0, 0, 0, 0.32);
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.script-card:hover {
  border-color: rgba(37, 99, 235, 0.45);
  transform: translateY(-2px);
  box-shadow: 0 22px 48px rgba(0, 0, 0, 0.5);
}

.script-card.is-selected {
  border-color: rgba(37, 99, 235, 0.65);
  background: linear-gradient(180deg, rgba(37, 99, 235, 0.12), rgba(37, 99, 235, 0.035));
  box-shadow: 0 22px 48px rgba(37, 99, 235, 0.22);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 10px;
}

.card-title {
  margin: 0;
  flex: 1;
  font-size: 15px;
  font-weight: 600;
  color: #e6edf3;
  line-height: 1.35;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-checkbox {
  flex-shrink: 0;
  margin-top: 2px;
}

.script-card :deep(.el-checkbox__inner) {
  background-color: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.22);
  border-radius: 4px;
}

.script-card :deep(.el-checkbox__inner:hover) {
  border-color: rgba(37, 99, 235, 0.65);
}

.script-card :deep(.el-checkbox.is-checked .el-checkbox__inner) {
  background-color: #2563eb;
  border-color: #2563eb;
}

.card-preview {
  margin: 0 0 12px;
  font-size: 12px;
  line-height: 1.6;
  color: #8b949e;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
}

.card-assets {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 14px;
  min-height: 26px;
}

.asset-chip {
  display: inline-flex;
  align-items: center;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 11px;
  line-height: 1.45;
  white-space: nowrap;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  color: #c5cdd6;
  transition: transform 0.15s ease;
}

.asset-chip:hover {
  transform: translateY(-1px);
}

.asset-chip--role {
  border-color: rgba(96, 165, 250, 0.32);
  background: rgba(96, 165, 250, 0.10);
  color: #93c5fd;
}

.asset-chip--scene {
  border-color: rgba(110, 231, 183, 0.30);
  background: rgba(110, 231, 183, 0.09);
  color: #6ee7b7;
}

.asset-chip--prop {
  border-color: rgba(252, 211, 77, 0.30);
  background: rgba(252, 211, 77, 0.09);
  color: #fcd34d;
}

.asset-chip--shot {
  border-color: rgba(196, 181, 253, 0.32);
  background: rgba(196, 181, 253, 0.10);
  color: #c4b5fd;
}

.asset-empty {
  font-size: 12px;
  color: #6e7681;
  padding: 3px 0;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 11px;
  line-height: 1.5;
  border: 1px solid transparent;
  font-variant-numeric: tabular-nums;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: currentColor;
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.04);
}

.status-chip.is-completed {
  border-color: rgba(110, 231, 183, 0.32);
  background: rgba(110, 231, 183, 0.10);
  color: #6ee7b7;
}

.status-chip.is-extracting {
  border-color: rgba(96, 165, 250, 0.32);
  background: rgba(96, 165, 250, 0.10);
  color: #93c5fd;
}

.status-chip.is-pending {
  border-color: rgba(255, 255, 255, 0.10);
  background: rgba(255, 255, 255, 0.04);
  color: #8b949e;
}

.status-chip.is-failed {
  border-color: rgba(248, 113, 113, 0.32);
  background: rgba(248, 113, 113, 0.10);
  color: #fca5a5;
}

.card-delete-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: #6e7681;
  cursor: pointer;
  transition: background 0.18s ease, color 0.18s ease, border-color 0.18s ease;
}

.card-delete-btn :deep(.el-icon) {
  font-size: 15px;
}

.card-delete-btn:hover {
  background: rgba(248, 113, 113, 0.10);
  color: #fca5a5;
  border-color: rgba(248, 113, 113, 0.32);
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
}
</style>

<style>
.script-sort-dropdown.el-popper {
  background-color: rgba(22, 27, 34, 0.96);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  box-shadow: 0 24px 50px rgba(0, 0, 0, 0.55);
  padding: 4px;
}

.script-sort-dropdown.el-popper .el-dropdown-menu {
  background: transparent;
  border: none;
  padding: 0;
}

.script-sort-dropdown.el-popper .el-dropdown-menu__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  min-width: 180px;
  margin: 2px 0;
  padding: 8px 12px;
  border-radius: 8px;
  color: #c5cdd6;
  font-size: 13px;
  line-height: 1.5;
}

.script-sort-dropdown.el-popper .el-dropdown-menu__item:not(.is-disabled):hover,
.script-sort-dropdown.el-popper .el-dropdown-menu__item:not(.is-disabled):focus {
  background-color: rgba(37, 99, 235, 0.12);
  color: #ffffff;
}

.script-sort-dropdown.el-popper .el-dropdown-menu__item.is-active {
  color: #93c5fd;
  background-color: rgba(37, 99, 235, 0.18);
}

.script-sort-dropdown.el-popper .el-dropdown-menu__item .el-icon {
  font-size: 12px;
}

.script-sort-dropdown.el-popper .el-popper__arrow::before {
  background-color: rgba(22, 27, 34, 0.96) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
}

/* 新建/编辑剧本弹窗（teleport 到 body，需置于非 scoped 块） */
.script-dark-dialog {
  background: linear-gradient(180deg, #12161b 0%, #0f141a 100%);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 24px;
  box-shadow: 0 30px 90px rgba(0, 0, 0, 0.55);
  overflow: hidden;
  color: #e6edf3;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
}

.script-dark-dialog .el-dialog__header {
  margin: 0;
  padding: 22px 28px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.script-dark-dialog .el-dialog__title {
  color: #f2f4f8;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.4px;
}

.script-dark-dialog .el-dialog__headerbtn {
  top: 16px;
  right: 20px;
  width: 36px;
  height: 36px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.02);
}

.script-dark-dialog .el-dialog__headerbtn .el-dialog__close {
  color: #8b949e;
  font-size: 20px;
}

.script-dark-dialog .el-dialog__headerbtn:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.18);
}

.script-dark-dialog .el-dialog__headerbtn:hover .el-dialog__close {
  color: #ffffff;
}

.script-dark-dialog .el-dialog__body {
  padding: 22px 28px 8px;
  color: #b8c2cc;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.14) transparent;
}

.script-dark-dialog .el-dialog__body::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.script-dark-dialog .el-dialog__body::-webkit-scrollbar-track {
  background: transparent;
}

.script-dark-dialog .el-dialog__body::-webkit-scrollbar-thumb {
  background-color: rgba(255, 255, 255, 0.12);
  border-radius: 999px;
  transition: background-color 0.18s ease;
}

.script-dark-dialog .el-dialog__body::-webkit-scrollbar-thumb:hover {
  background-color: rgba(255, 255, 255, 0.24);
}

.script-dark-dialog .el-dialog__footer {
  padding: 16px 28px 22px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.script-dark-dialog .el-form-item__label {
  color: #d5dce4;
  font-size: 14px;
  font-weight: 600;
  padding: 0 0 8px;
}

.script-dark-dialog .el-input__wrapper {
  min-height: 42px;
  padding: 0 14px;
  background-color: #0c1015;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.12) inset;
  border-radius: 10px;
  color: #e6edf3;
  font-size: 14px;
}

.script-dark-dialog .el-textarea__inner {
  min-height: 96px;
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

.script-dark-dialog .el-input__wrapper:hover,
.script-dark-dialog .el-textarea__inner:hover {
  background-color: #0e131a;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.22) inset;
}

.script-dark-dialog .el-input__wrapper.is-focus,
.script-dark-dialog .el-textarea__inner:focus {
  background-color: #0d1219;
  box-shadow:
    0 0 0 1px rgba(37, 99, 235, 0.55) inset,
    0 0 0 3px rgba(37, 99, 235, 0.12);
}

.script-dark-dialog .el-input__inner,
.script-dark-dialog .el-textarea__inner {
  color: #e6edf3;
}

.script-dark-dialog .el-input__inner::placeholder,
.script-dark-dialog .el-textarea__inner::placeholder {
  color: #7e8893;
}

.script-dark-dialog .el-input__count,
.script-dark-dialog .el-input__count-inner,
.script-dark-dialog .el-input .el-input__count,
.script-dark-dialog .el-textarea .el-input__count {
  color: #6e7681 !important;
  background: transparent !important;
  background-color: transparent !important;
  font-size: 12px;
}

.script-dark-dialog .el-textarea .el-input__count {
  bottom: 8px;
  right: 12px;
}

.script-dark-dialog .el-form-item__error {
  color: #fca5a5;
}

.script-dark-dialog .el-form-item__content {
  width: 100%;
  display: block;
}

.script-dark-dialog .markdown-editor-shell,
.script-dark-dialog .markdown-editor-instance {
  width: 100%;
  box-sizing: border-box;
}

.script-dark-dialog .script-asset-select {
  width: 100%;
}

.script-dark-dialog .el-select__wrapper {
  min-height: 42px;
  padding: 4px 14px;
  background-color: #0c1015;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.12) inset;
  border-radius: 10px;
  color: #e6edf3;
  font-size: 14px;
}

.script-dark-dialog .el-select__wrapper:hover {
  background-color: #0e131a;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.22) inset;
}

.script-dark-dialog .el-select__wrapper.is-focused {
  background-color: #0d1219;
  box-shadow:
    0 0 0 1px rgba(37, 99, 235, 0.55) inset,
    0 0 0 3px rgba(37, 99, 235, 0.12);
}

.script-dark-dialog .el-select__wrapper .el-select__placeholder {
  color: #7e8893;
}

.script-dark-dialog .el-dialog__footer .el-button {
  height: 40px;
  min-width: 88px;
  padding: 0 20px;
  border-radius: 10px;
  font-weight: 700;
}

.script-dark-dialog .el-dialog__footer .el-button:not(.el-button--primary) {
  background-color: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.12);
  color: #e6edf3;
}

.script-dark-dialog .el-dialog__footer .el-button:not(.el-button--primary):hover {
  background-color: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.22);
  color: #ffffff;
}

.script-dark-dialog .el-dialog__footer .el-button--primary {
  background-color: #2563eb;
  border-color: #2563eb;
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.18);
}

.script-dark-dialog .el-dialog__footer .el-button--primary:hover {
  background-color: #1d4ed8;
  border-color: #1d4ed8;
}

/* 删除确认弹窗暗色样式 */
.script-dark-messagebox {
  background: linear-gradient(180deg, #14181f 0%, #0d1117 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.55);
  color: #e6edf3;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
}

.script-dark-messagebox .el-message-box__header {
  padding: 18px 24px 8px;
}

.script-dark-messagebox .el-message-box__title {
  color: #e6edf3;
  font-weight: 700;
}

.script-dark-messagebox .el-message-box__content {
  padding: 8px 24px 18px;
  color: #b8c2cc;
}

.script-dark-messagebox .el-message-box__btns {
  padding: 12px 24px 18px;
  background: rgba(255, 255, 255, 0.015);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.script-dark-messagebox .el-message-box__btns .el-button {
  border-radius: 8px;
}

.script-dark-messagebox .el-message-box__btns .el-button:not(.el-button--primary):not(.el-button--danger) {
  background-color: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
  color: #c5cdd6;
}

.script-dark-messagebox .el-message-box__btns .el-button:not(.el-button--primary):not(.el-button--danger):hover {
  background-color: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.18);
  color: #ffffff;
}

/* 关联资产多选浮层（teleport 到 body，需置于非 scoped 块） */
.script-dark-select.el-popper {
  background-color: #14181f;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.45);
  color: #e6edf3;
}

.script-dark-select.el-popper .el-select-dropdown__list {
  padding: 6px 4px;
}

.script-dark-select.el-popper .el-select-dropdown__item {
  color: #c5cdd6;
  border-radius: 8px;
  margin: 2px 4px;
  padding: 0 12px;
  height: 36px;
  line-height: 36px;
}

.script-dark-select.el-popper .el-select-dropdown__item:hover,
.script-dark-select.el-popper .el-select-dropdown__item.is-hovering {
  background-color: rgba(255, 255, 255, 0.06);
  color: #ffffff;
}

.script-dark-select.el-popper .el-select-dropdown__item.is-selected {
  color: #93c5fd;
  background-color: rgba(37, 99, 235, 0.16);
  font-weight: 600;
}

.script-dark-select.el-popper .el-select-dropdown__item.is-selected::after {
  color: #93c5fd;
}

.script-dark-select.el-popper .el-select-dropdown__empty {
  color: #7e8893;
  padding: 14px 0;
  font-size: 13px;
}

.script-dark-select.el-popper .el-popper__arrow::before {
  background-color: #14181f;
  border-color: rgba(255, 255, 255, 0.08);
}

.script-dark-select .asset-option {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  overflow: hidden;
}

.script-dark-select .asset-option__type {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 36px;
  height: 20px;
  padding: 0 6px;
  border-radius: 6px;
  border: 1px solid transparent;
  font-size: 11px;
  font-weight: 600;
  line-height: 1;
}

.script-dark-select .asset-option__type--role {
  border-color: rgba(96, 165, 250, 0.32);
  background: rgba(96, 165, 250, 0.12);
  color: #93c5fd;
}

.script-dark-select .asset-option__type--scene {
  border-color: rgba(110, 231, 183, 0.30);
  background: rgba(110, 231, 183, 0.10);
  color: #6ee7b7;
}

.script-dark-select .asset-option__type--prop {
  border-color: rgba(252, 211, 77, 0.30);
  background: rgba(252, 211, 77, 0.10);
  color: #fcd34d;
}

.script-dark-select .asset-option__type--shot {
  border-color: rgba(196, 181, 253, 0.32);
  background: rgba(196, 181, 253, 0.12);
  color: #c4b5fd;
}

.script-dark-select .asset-option__name {
  color: #e6edf3;
  font-weight: 500;
  flex-shrink: 0;
}

.script-dark-select .asset-option__desc {
  color: #7e8893;
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.script-dark-select.el-popper .el-select-group__title {
  color: #7e8893;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.4px;
  padding: 10px 12px 4px;
}

.script-dark-select.el-popper .el-select-group__wrap:not(:last-of-type)::after {
  background-color: rgba(255, 255, 255, 0.06);
}

/* collapse-tags-tooltip 浮层（鼠标 hover 已选 + N 标签时显示全部已选项） */
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

/* 多选 collapse-tags 内 el-tag 暗色覆盖（默认浅色背景修正） */
.script-dark-dialog .el-select__wrapper .el-tag,
.script-import-dialog .el-select__wrapper .el-tag,
.script-dark-dialog .el-select__selected-item .el-tag,
.script-import-dialog .el-select__selected-item .el-tag {
  background-color: rgba(37, 99, 235, 0.18) !important;
  border: 1px solid rgba(37, 99, 235, 0.32) !important;
  color: #c5d4ed !important;
  border-radius: 6px;
}

.script-dark-dialog .el-select__wrapper .el-tag .el-tag__content,
.script-import-dialog .el-select__wrapper .el-tag .el-tag__content,
.script-dark-dialog .el-select__wrapper .el-select__tags-text,
.script-import-dialog .el-select__wrapper .el-select__tags-text {
  color: #c5d4ed;
}

.script-dark-dialog .el-select__wrapper .el-tag .el-tag__close,
.script-import-dialog .el-select__wrapper .el-tag .el-tag__close {
  color: #93b4ec;
  background-color: transparent;
}

.script-dark-dialog .el-select__wrapper .el-tag .el-tag__close:hover,
.script-import-dialog .el-select__wrapper .el-tag .el-tag__close:hover {
  background-color: rgba(37, 99, 235, 0.42);
  color: #ffffff;
}

/* ============ 导入剧本弹窗（teleport 到 body，需置于非 scoped 块） ============ */
.script-import-dialog .el-dialog__header {
  padding: 18px 28px 12px;
}

.script-import-dialog .el-dialog__title {
  font-size: 19px;
}

.script-import-dialog .el-dialog__headerbtn {
  top: 12px;
}

.script-import-dialog .import-steps {
  padding: 4px 12px 18px;
}

.script-import-dialog .import-steps .el-step__title {
  color: #8b949e;
  font-size: 13px;
  font-weight: 500;
}

.script-import-dialog .import-steps .el-step__head.is-process .el-step__icon,
.script-import-dialog .import-steps .el-step__head.is-finish .el-step__icon {
  background-color: rgba(37, 99, 235, 0.18);
  border-color: rgba(37, 99, 235, 0.55);
  color: #93c5fd;
}

.script-import-dialog .import-steps .el-step__head.is-success .el-step__icon {
  background-color: rgba(34, 197, 94, 0.16);
  border-color: rgba(34, 197, 94, 0.55);
  color: #86efac;
}

.script-import-dialog .import-steps .el-step__title.is-process,
.script-import-dialog .import-steps .el-step__title.is-success {
  color: #e6edf3;
  font-weight: 600;
}

.script-import-dialog .import-steps .el-step__line {
  background-color: rgba(255, 255, 255, 0.08);
}

.script-import-dialog .import-steps .el-step__head.is-wait .el-step__icon {
  background-color: #0c1015;
  border-color: rgba(255, 255, 255, 0.18);
  color: #6e7681;
}

.script-import-dialog .import-steps .el-step__icon-inner {
  color: inherit;
  font-weight: 600;
}

.script-import-dialog .import-steps .el-step__title.is-wait {
  color: #6e7681;
}

.script-import-dialog .import-step {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.script-import-dialog .import-mode {
  align-self: flex-start;
  display: inline-flex;
  padding: 3px;
  gap: 2px;
  background-color: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
}

.script-import-dialog .import-mode .el-radio-button {
  margin: 0;
}

.script-import-dialog .import-mode .el-radio-button__inner,
.script-import-dialog .import-mode .el-radio-button:first-child .el-radio-button__inner,
.script-import-dialog .import-mode .el-radio-button:not(:first-child) .el-radio-button__inner,
.script-import-dialog .import-mode .el-radio-button:last-child .el-radio-button__inner {
  background-color: transparent;
  border: none !important;
  border-radius: 7px !important;
  color: #c5cdd6;
  font-size: 13px;
  height: 30px;
  line-height: 30px;
  padding: 0 14px;
  box-shadow: none !important;
  outline: none !important;
  transition: background-color 0.18s ease, color 0.18s ease;
}

.script-import-dialog .import-mode .el-radio-button__inner:hover {
  background-color: rgba(255, 255, 255, 0.06);
  color: #ffffff;
  border: none !important;
  box-shadow: none !important;
  outline: none !important;
}

.script-import-dialog .import-mode .el-radio-button__original-radio:checked + .el-radio-button__inner,
.script-import-dialog .import-mode .el-radio-button__original-radio:checked + .el-radio-button__inner:hover {
  background-color: rgba(37, 99, 235, 0.22);
  border: none !important;
  color: #93c5fd;
  box-shadow: none !important;
  outline: none !important;
}

.script-import-dialog .import-mode .el-radio-button__original-radio:focus-visible + .el-radio-button__inner {
  outline: 1px solid rgba(96, 165, 250, 0.45) !important;
  outline-offset: 1px;
  box-shadow: none !important;
  border: none !important;
}

.script-import-dialog .import-mode__hint {
  margin: -6px 0 0;
  color: #7e8893;
  font-size: 12px;
  line-height: 1.5;
}

.script-import-dialog .import-uploader .el-upload-dragger {
  padding: 6px 24px;
  background-color: #0c1015;
  border: 1.5px dashed rgba(255, 255, 255, 0.18);
  border-radius: 14px;
  transition: background-color 0.18s ease, border-color 0.18s ease;
}

.script-import-dialog .import-uploader .el-upload-dragger:hover,
.script-import-dialog .import-uploader .el-upload-dragger.is-dragover {
  background-color: rgba(37, 99, 235, 0.06);
  border-color: rgba(96, 165, 250, 0.55);
}

.script-import-dialog .import-uploader__icon {
  font-size: 32px;
  color: #93c5fd;
}

.script-import-dialog .import-uploader__text {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: #c5cdd6;
}

.script-import-dialog .import-uploader__text strong {
  font-size: 14px;
  font-weight: 600;
  color: #e6edf3;
}

.script-import-dialog .import-uploader__text span {
  font-size: 12px;
  color: #6e7681;
}

.script-import-dialog .import-uploader__file {
  margin-top: 10px;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
  background: rgba(37, 99, 235, 0.12);
  border: 1px solid rgba(37, 99, 235, 0.32);
  color: #93c5fd;
  display: inline-block;
}

.script-import-dialog .import-divider {
  margin: 4px 0;
  background-color: transparent;
}

.script-import-dialog .import-divider .el-divider__text {
  color: #6e7681;
  font-size: 12px;
  background-color: transparent;
  padding: 0 12px;
}

.script-import-dialog .import-divider.el-divider--horizontal {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  height: 1px;
}

.script-import-dialog .import-meta {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
  padding: 10px 0 0;
  color: #8b949e;
  font-size: 12px;
}

.script-import-dialog .import-meta strong {
  color: #e6edf3;
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
  font-weight: 600;
  margin: 0 2px;
}

.script-import-dialog .import-meta__warn {
  color: #fca5a5;
}

.script-import-dialog .import-bulk {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.02);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.script-import-dialog .import-bulk__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.script-import-dialog .import-bulk__title {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: #f2f4f8;
}

.script-import-dialog .import-bulk__count {
  font-size: 12px;
  color: #7e8893;
}

.script-import-dialog .import-bulk__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 280px;
  overflow-y: auto;
}

.script-import-dialog .import-bulk__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  position: relative;
  transition: background-color 0.18s ease, border-color 0.18s ease, transform 0.18s ease, opacity 0.18s ease;
}

.script-import-dialog .import-bulk__item:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.12);
}

.script-import-dialog .import-bulk__item.is-dragging {
  opacity: 0.45;
  transform: scale(0.99);
  cursor: grabbing;
}

.script-import-dialog .import-bulk__item.is-drop-before::before,
.script-import-dialog .import-bulk__item.is-drop-after::after {
  content: "";
  position: absolute;
  left: 12px;
  right: 12px;
  height: 2px;
  border-radius: 2px;
  background: linear-gradient(90deg, rgba(37, 99, 235, 0.1), #60a5fa, rgba(37, 99, 235, 0.1));
  box-shadow: 0 0 8px rgba(96, 165, 250, 0.55);
}

.script-import-dialog .import-bulk__item.is-drop-before::before {
  top: -3px;
}

.script-import-dialog .import-bulk__item.is-drop-after::after {
  bottom: -3px;
}

.script-import-dialog .import-bulk__handle {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #6e7681;
  cursor: grab;
  border-radius: 6px;
  transition: color 0.18s ease, background-color 0.18s ease;
}

.script-import-dialog .import-bulk__handle:hover {
  color: #c5cdd6;
  background-color: rgba(255, 255, 255, 0.05);
}

.script-import-dialog .import-bulk__handle:active {
  cursor: grabbing;
}

.script-import-dialog .import-bulk__handle .el-icon {
  font-size: 16px;
}

.script-import-dialog .import-bulk__main {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.script-import-dialog .import-bulk__seq {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: #93c5fd;
  background: rgba(37, 99, 235, 0.16);
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
}

.script-import-dialog .import-bulk__info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.script-import-dialog .import-bulk__name {
  font-size: 13px;
  font-weight: 600;
  color: #e6edf3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.script-import-dialog .import-bulk__meta {
  font-size: 11px;
  color: #7e8893;
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
}

/* 切分规则 */
.script-import-dialog .import-split {
  padding: 14px 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.02);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.script-import-dialog .import-split__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
}

.script-import-dialog .import-split__title {
  margin: 0 0 2px;
  font-size: 14px;
  font-weight: 700;
  color: #f2f4f8;
}

.script-import-dialog .import-split__hint {
  margin: 0;
  font-size: 12px;
  color: #6e7681;
  line-height: 1.5;
}

.script-import-dialog .import-split__main {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.script-import-dialog .import-split__select {
  width: 280px;
}

.script-import-dialog .import-split__opt {
  display: flex;
  flex-direction: column;
  line-height: 1.4;
}

.script-import-dialog .import-split__opt-label {
  color: inherit;
  font-size: 13px;
  font-weight: 600;
}

.script-import-dialog .import-split__opt-desc {
  color: #6e7681;
  font-size: 11px;
}

.script-import-dialog .import-split__editor {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.script-import-dialog .import-split__row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
}

.script-import-dialog .import-split__row-label {
  flex-shrink: 0;
  width: 48px;
  font-size: 12px;
  font-weight: 600;
  color: #c5cdd6;
  text-align: right;
}

.script-import-dialog .import-split__row-pattern {
  flex: 1;
  min-width: 240px;
}

.script-import-dialog .import-split__row-flags {
  width: 200px;
  flex-shrink: 0;
}

/* 预览区表格 */
.script-import-dialog .import-preview__head {
  color: #c5cdd6;
  font-size: 13px;
  padding: 4px 4px 8px;
}

.script-import-dialog .import-preview__head strong {
  color: #93c5fd;
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
  margin: 0 2px;
}

.script-import-dialog .script-import-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: rgba(255, 255, 255, 0.03);
  --el-table-row-hover-bg-color: rgba(37, 99, 235, 0.06);
  --el-table-border-color: rgba(255, 255, 255, 0.06);
  --el-table-header-text-color: #c5cdd6;
  --el-table-text-color: #e6edf3;
  --el-table-fixed-box-shadow: none;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  overflow: hidden;
  background-color: #0c1015;
}

.script-import-dialog .script-import-table,
.script-import-dialog .script-import-table tr,
.script-import-dialog .script-import-table th.el-table__cell,
.script-import-dialog .script-import-table td.el-table__cell {
  background-color: transparent;
  color: #e6edf3;
  border-color: rgba(255, 255, 255, 0.06);
}

.script-import-dialog .script-import-table thead th.el-table__cell {
  background-color: rgba(255, 255, 255, 0.03);
  color: #c5cdd6;
  font-size: 12px;
  font-weight: 600;
}

.script-import-dialog .script-import-table tbody tr:hover > td.el-table__cell {
  background-color: rgba(37, 99, 235, 0.06);
}

.script-import-dialog .script-import-table .el-table__inner-wrapper::before {
  display: none;
}

.script-import-dialog .script-import-table .el-table__body-wrapper,
.script-import-dialog .script-import-table .el-table__header-wrapper,
.script-import-dialog .script-import-table .el-table__inner-wrapper {
  background-color: transparent;
}

.script-import-dialog .script-import-table .el-table__empty-block {
  background-color: transparent;
  color: #6e7681;
}

.script-import-dialog .script-import-table .el-table__empty-text {
  color: #6e7681;
}

.script-import-dialog .script-import-table .el-checkbox__inner {
  background-color: #0c1015;
  border-color: rgba(255, 255, 255, 0.22);
}

.script-import-dialog .script-import-table .el-checkbox__inner:hover {
  border-color: rgba(96, 165, 250, 0.6);
}

.script-import-dialog .script-import-table .el-checkbox.is-checked .el-checkbox__inner,
.script-import-dialog .script-import-table .el-checkbox.is-indeterminate .el-checkbox__inner {
  background-color: #2563eb;
  border-color: #2563eb;
}

.script-import-dialog .script-import-table .el-checkbox.is-checked .el-checkbox__inner::after {
  border-color: #ffffff;
}

.script-import-dialog .script-import-table .el-checkbox.is-indeterminate .el-checkbox__inner::before {
  background-color: #ffffff;
}

.script-import-dialog .script-import-table .row-count {
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
  color: #93c5fd;
  font-size: 12px;
}

.script-import-dialog .script-import-table .row-edit-btn {
  height: auto;
  padding: 2px 6px;
  background: transparent;
  border: none;
  box-shadow: none;
  color: #93c5fd;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.script-import-dialog .script-import-table .row-edit-btn:hover {
  color: #bfdbfe;
  background: rgba(37, 99, 235, 0.12);
  transform: none;
}

.script-import-dialog .script-import-table .row-edit-btn .el-icon {
  font-size: 14px;
}

/* 导入弹窗内部按钮统一为黑雅风格 */
.script-import-dialog .el-dialog__body .el-button {
  height: 30px;
  padding: 0 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  background-color: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.12);
  color: #c5cdd6;
  transition: background-color 0.18s ease, border-color 0.18s ease, color 0.18s ease, transform 0.18s ease;
}

.script-import-dialog .el-dialog__body .el-button:hover,
.script-import-dialog .el-dialog__body .el-button:focus {
  background-color: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.22);
  color: #ffffff;
  transform: translateY(-1px);
}

.script-import-dialog .el-dialog__body .el-button:active {
  transform: translateY(0);
}

.script-import-dialog .el-dialog__body .el-button.is-disabled,
.script-import-dialog .el-dialog__body .el-button.is-disabled:hover,
.script-import-dialog .el-dialog__body .el-button.is-disabled:focus {
  background-color: rgba(255, 255, 255, 0.02);
  border-color: rgba(255, 255, 255, 0.06);
  color: #4d5560;
  transform: none;
  cursor: not-allowed;
}

.script-import-dialog .el-dialog__body .el-button--primary {
  background-color: #2563eb;
  border-color: #2563eb;
  color: #ffffff;
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.22);
}

.script-import-dialog .el-dialog__body .el-button--primary:hover,
.script-import-dialog .el-dialog__body .el-button--primary:focus {
  background-color: #1d4ed8;
  border-color: #1d4ed8;
  color: #ffffff;
}

.script-import-dialog .el-dialog__body .el-button--primary.is-plain {
  background-color: rgba(37, 99, 235, 0.1);
  border-color: rgba(37, 99, 235, 0.45);
  color: #93c5fd;
  box-shadow: none;
}

.script-import-dialog .el-dialog__body .el-button--primary.is-plain:hover,
.script-import-dialog .el-dialog__body .el-button--primary.is-plain:focus {
  background-color: rgba(37, 99, 235, 0.2);
  border-color: rgba(37, 99, 235, 0.65);
  color: #ffffff;
}

.script-import-dialog .el-dialog__body .el-button.is-link {
  height: auto;
  padding: 2px 4px;
  background: transparent;
  border: none;
  box-shadow: none;
}

.script-import-dialog .el-dialog__body .el-button.is-link.el-button--danger {
  color: #fca5a5;
}

.script-import-dialog .el-dialog__body .el-button.is-link.el-button--danger:hover {
  color: #fecaca;
  background: transparent;
  transform: none;
}

.script-import-dialog .el-dialog__body .el-button .el-icon {
  margin-right: 2px;
}

/* 单元格 tooltip 深色 */
.script-cell-tooltip.is-dark {
  background: linear-gradient(180deg, #14181f 0%, #0d1117 100%);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #e6edf3;
  font-size: 12px;
}

/* 预览阶段单集剧本编辑弹窗（嵌套于导入弹窗之上） */
.script-preview-edit-dialog .preview-edit__meta {
  margin-top: 4px;
  padding: 8px 12px;
  border-radius: 10px;
  background: rgba(37, 99, 235, 0.08);
  border: 1px solid rgba(37, 99, 235, 0.18);
  color: #93c5fd;
  font-size: 12px;
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
}
</style>
