<template>
  <main class="project-page">
    <div class="app-shell">
      <aside class="sidebar">
        <div class="side-top">
          <div class="brand" @click="goHome">AF</div>

          <el-tooltip content="项目" placement="right">
            <button class="nav-btn active" aria-label="项目" @click="router.push('/projects')">
              <el-icon><Folder /></el-icon>
            </button>
          </el-tooltip>

          <el-tooltip content="列表" placement="right">
            <button class="nav-btn" aria-label="列表" @click="router.push('/tasks')">
              <el-icon><List /></el-icon>
            </button>
          </el-tooltip>
        </div>

        <div class="side-bottom">
          <el-tooltip content="文档" placement="right">
            <button class="nav-btn" aria-label="文档" @click="router.push('/docs')">
              <el-icon><Document /></el-icon>
            </button>
          </el-tooltip>

          <el-tooltip content="设置" placement="right">
            <button class="nav-btn" aria-label="设置" @click="router.push('/settings')">
              <el-icon><Setting /></el-icon>
            </button>
          </el-tooltip>

          <el-tooltip content="代码仓库" placement="right">
            <button class="nav-btn" aria-label="代码仓库" @click="router.push('/repository')">
              <el-icon><Connection /></el-icon>
            </button>
          </el-tooltip>
        </div>
      </aside>

      <section class="main-panel">
        <header class="page-header">
          <div>
            <h1 class="title">我的项目</h1>
            <p class="desc">管理您的所有短剧项目</p>
          </div>

          <el-button class="create-button" type="primary" size="large" @click="handleCreateProject">
            <el-icon><Plus /></el-icon>
            新建项目
          </el-button>
        </header>

        <section class="project-grid">
          <el-card
            v-for="project in pagedProjects"
            :key="project.id"
            class="project-card"
            shadow="never"
          >
            <template #header>
              <div class="card-head">
                <h2 class="project-name">{{ project.name }}</h2>
                <el-tag class="source-tag" effect="plain" round>{{ project.source }}</el-tag>
              </div>
            </template>

            <el-tag class="model-tag" type="primary" effect="plain" round>
              {{ project.model }}
            </el-tag>

            <p class="summary">{{ project.summary }}</p>

            <footer class="card-footer">
              <time class="time">{{ project.createdAt }}</time>

              <div class="actions">
                <el-tooltip content="编辑" placement="top">
                  <el-button text circle class="icon-action" @click="handleEditProject(project.id)">
                    <el-icon><EditPen /></el-icon>
                  </el-button>
                </el-tooltip>

                <el-tooltip content="删除" placement="top">
                  <el-button text circle class="icon-action delete" @click="handleDeleteProject(project.id)">
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </el-tooltip>
              </div>
            </footer>
          </el-card>
        </section>

        <div class="pagination-wrap">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="projects.length"
            layout="prev, pager, next, total"
            background
          />
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Connection,
  Delete,
  Document,
  EditPen,
  Folder,
  List,
  Plus,
  Setting,
} from '@element-plus/icons-vue'

interface ProjectItem {
  id: number
  name: string
  source: string
  model: string
  summary: string
  createdAt: string
}

const router = useRouter()

const currentPage = ref(1)
const pageSize = ref(4)

const projects = ref<ProjectItem[]>([
  {
    id: 1,
    name: '诛仙',
    source: '基于小说原文',
    model: '3D_chinese_traditional',
    summary:
      '《诛仙》是由萧鼎创作的经典仙侠小说，围绕草庙村少年张小凡的成长与命运展开，兼具仙侠世界观、门派冲突与人物情感张力，适合改编为连续型短剧项目。',
    createdAt: '2026-04-20 21:17:50',
  },
  {
    id: 2,
    name: '庆余年',
    source: '基于小说原文',
    model: '3D_chinese_traditional',
    summary:
      '《庆余年》是一部融合权谋、成长与家国叙事的长篇历史幻想小说，人物关系复杂，剧情推进紧凑，适合拆分成高反转、强节奏的剧集型内容。',
    createdAt: '2026-04-19 18:42:33',
  },
  {
    id: 3,
    name: '完美世界',
    source: '基于小说原文',
    model: '3D_xianxia',
    summary:
      '《完美世界》构建了宏大的东方玄幻世界，以少年石昊的成长冒险为主线，兼具热血、修行与世界观扩张，适合多角色并行展开与分篇章创作。',
    createdAt: '2026-04-18 15:09:21',
  },
  {
    id: 4,
    name: '斗破苍穹',
    source: '基于小说原文',
    model: '3D_xianxia',
    summary:
      '《斗破苍穹》以天才少年跌落谷底后重返巅峰为主线，节奏明快、升级清晰、冲突密集，非常适合短剧化拆分与高密度爽点表达。',
    createdAt: '2026-04-17 12:31:08',
  },
])

const pagedProjects = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return projects.value.slice(start, start + pageSize.value)
})

const goHome = () => {
  router.push('/projects')
}

const handleCreateProject = () => {
  router.push('/projects/create')
}

const handleEditProject = (id: number) => {
  router.push({ name: 'ProjectEdit', params: { id } })
}

const handleDeleteProject = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个项目吗？删除后不可恢复。', '删除项目', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger',
    })

    projects.value = projects.value.filter((project) => project.id !== id)

    const maxPage = Math.max(1, Math.ceil(projects.value.length / pageSize.value))
    if (currentPage.value > maxPage) {
      currentPage.value = maxPage
    }

    ElMessage.success('项目已删除')
  } catch {
    // 用户取消删除时不做提示。
  }
}
</script>

<style scoped>
.project-page {
  min-height: 100vh;
  padding: 20px;
  color: #e6edf3;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
  background:
    radial-gradient(circle at top, rgba(100, 116, 139, 0.18) 0%, rgba(11, 13, 16, 0) 32%),
    linear-gradient(180deg, #0d1117 0%, #0b0d10 100%);
}

.app-shell {
  min-height: calc(100vh - 40px);
  display: grid;
  grid-template-columns: 84px 1fr;
  gap: 18px;
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
  color: #111827;
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.5px;
  cursor: pointer;
  user-select: none;
  background: linear-gradient(135deg, #f3d96b, #c4b5fd);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
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
  transition: 0.2s ease;
}

.nav-btn .el-icon {
  font-size: 22px;
}

.nav-btn:hover {
  color: #e6edf3;
  background: rgba(255, 255, 255, 0.04);
}

.nav-btn.active {
  color: #dbeafe;
  border-color: rgba(37, 99, 235, 0.32);
  background: linear-gradient(180deg, rgba(37, 99, 235, 0.22), rgba(37, 99, 235, 0.12));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.main-panel {
  padding: 34px 36px 28px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 28px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.025), rgba(255, 255, 255, 0.015));
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.45);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
  margin-bottom: 28px;
}

.title {
  margin: 0;
  font-size: 48px;
  line-height: 1.06;
  font-weight: 800;
  letter-spacing: -0.8px;
}

.desc {
  margin: 8px 0 0;
  color: #8b949e;
  font-size: 18px;
}

.create-button {
  height: 44px;
  padding: 0 18px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  background: #2563eb;
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.18);
}

.create-button:hover,
.create-button:focus {
  background: #1d4ed8;
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(320px, 1fr));
  gap: 22px 28px;
}

.project-card {
  min-height: 236px;
  display: flex;
  flex-direction: column;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.022), rgba(255, 255, 255, 0.012));
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.18);
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.project-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.18);
  box-shadow: 0 18px 34px rgba(0, 0, 0, 0.24);
}

.project-card :deep(.el-card__header) {
  padding: 28px 28px 0;
  border-bottom: 0;
}

.project-card :deep(.el-card__body) {
  display: flex;
  flex: 1;
  flex-direction: column;
  padding: 14px 28px 24px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.project-name {
  margin: 0;
  color: #e6edf3;
  font-size: 24px;
  font-weight: 800;
  line-height: 1.2;
}

.source-tag {
  height: 32px;
  padding: 0 14px;
  color: #d1d5db;
  border-color: rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.06);
  white-space: nowrap;
}

.model-tag {
  width: fit-content;
  height: 32px;
  padding: 0 14px;
  color: #c7d2fe;
  border-color: rgba(37, 99, 235, 0.18);
  background: rgba(37, 99, 235, 0.12);
}

.summary {
  flex: 1;
  margin: 16px 0 0;
  color: #d7dee7;
  font-size: 15px;
  line-height: 1.9;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 22px;
}

.time {
  color: #8b949e;
  font-size: 14px;
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-action {
  width: 34px;
  height: 34px;
  color: #8b949e;
  border-radius: 10px;
}

.icon-action:hover {
  color: #e6edf3;
  background: rgba(255, 255, 255, 0.05);
}

.icon-action.delete:hover {
  color: #fca5a5;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}

.pagination-wrap :deep(.el-pagination.is-background .btn-prev),
.pagination-wrap :deep(.el-pagination.is-background .btn-next),
.pagination-wrap :deep(.el-pagination.is-background .el-pager li) {
  color: #8b949e;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.02);
}

.pagination-wrap :deep(.el-pagination.is-background .el-pager li.is-active) {
  color: #fff;
  border-color: #2563eb;
  background: #2563eb;
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.18);
}

.pagination-wrap :deep(.el-pagination__total) {
  color: #8b949e;
}

@media (max-width: 1180px) {
  .title {
    font-size: 42px;
  }

  .project-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 820px) {
  .project-page {
    padding: 14px;
  }

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

  .main-panel {
    padding: 24px 18px 22px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .title {
    font-size: 34px;
  }

  .desc {
    font-size: 15px;
  }

  .create-button {
    align-self: flex-start;
  }

  .project-card {
    min-height: auto;
  }

  .project-card :deep(.el-card__header) {
    padding: 22px 18px 0;
  }

  .project-card :deep(.el-card__body) {
    padding: 14px 18px 18px;
  }

  .card-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .card-footer {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>