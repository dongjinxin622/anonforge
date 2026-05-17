<template>
  <main class="project-page">
    <div class="app-shell">
      <aside class="sidebar">
        <div class="side-top">
          <div class="brand" @click="goHome">AF</div>

          <el-tooltip content="项目" placement="right">
            <button class="nav-btn active" aria-label="项目" @click="router.push('/project')">
              <el-icon><Folder /></el-icon>
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
            <button class="nav-btn" aria-label="设置" @click="showComingSoon">
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
          <div>
            <h1 class="title">我的项目</h1>
            <p class="desc">管理项目、生成模式、状态和协作成员</p>
          </div>

          <el-button class="create-button" type="primary" size="large" @click="openCreateDialog">
            <el-icon><Plus /></el-icon>
            新建项目
          </el-button>
        </header>

        <section class="toolbar">
          <el-input
            v-model="searchKeyword"
            class="search-input"
            clearable
            placeholder="按项目名称搜索"
            @clear="loadProjects"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <el-button :loading="loading" @click="handleSearch">搜索</el-button>
          <el-button :loading="loading" @click="loadProjects">刷新</el-button>
        </section>

        <section
          v-loading="loading"
          class="project-grid"
          element-loading-background="rgba(13, 17, 23, 0.55)"
        >
          <el-empty
            v-if="!loading && projects.length === 0"
            class="empty-state"
            description="暂无项目"
          />

          <el-card
            v-for="project in pagedProjects"
            v-else
            :key="project.public_id"
            class="project-card"
            shadow="never"
          >
            <template #header>
              <div class="card-head">
                <h2 class="project-name">{{ project.name }}</h2>
                <el-tag class="source-tag" effect="plain" round>{{ contentTypeLabel(project.content_type) }}</el-tag>
              </div>
            </template>

            <div class="tag-row">
              <el-tag class="model-tag" type="primary" effect="plain" round>
                {{ project.art_style || '未设置风格' }}
              </el-tag>
              <el-tag class="ratio-tag" effect="plain" round>
                {{ project.video_ratio }}
              </el-tag>
              <el-tag :type="project.disabled_at ? 'danger' : 'success'" effect="plain" round>
                {{ project.disabled_at ? '已禁用' : '可用' }}
              </el-tag>
            </div>

            <p class="summary">{{ project.intro || '暂无简介' }}</p>

            <footer class="card-footer">
              <time class="time">{{ formatDate(project.created_at) }}</time>

              <div class="actions">
                <el-tooltip content="成员" placement="top">
                  <el-button text circle class="icon-action" @click="openMemberDialog(project)">
                    <el-icon><UserFilled /></el-icon>
                  </el-button>
                </el-tooltip>

                <el-tooltip :content="project.disabled_at ? '启用' : '禁用'" placement="top">
                  <el-button text circle class="icon-action" @click="toggleProjectStatus(project)">
                    <el-icon><SwitchButton /></el-icon>
                  </el-button>
                </el-tooltip>

                <el-tooltip content="编辑" placement="top">
                  <el-button text circle class="icon-action" @click="openEditDialog(project)">
                    <el-icon><EditPen /></el-icon>
                  </el-button>
                </el-tooltip>

                <el-tooltip content="删除" placement="top">
                  <el-button text circle class="icon-action delete" @click="handleDeleteProject(project)">
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

    <el-dialog
      v-model="projectDialogVisible"
      :title="projectDialogTitle"
      width="720px"
      destroy-on-close
    >
      <el-form
        ref="projectFormRef"
        :model="projectForm"
        :rules="projectRules"
        class="project-form"
        label-width="110px"
      >
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="projectForm.name" maxlength="100" show-word-limit />
        </el-form-item>

        <el-form-item label="项目简介" prop="intro">
          <el-input v-model="projectForm.intro" maxlength="2000" rows="4" show-word-limit type="textarea" />
        </el-form-item>

        <div class="form-grid">
          <el-form-item label="项目类型" prop="project_type">
            <el-input v-model="projectForm.project_type" />
          </el-form-item>

          <el-form-item label="内容类型" prop="content_type">
            <el-input v-model="projectForm.content_type" />
          </el-form-item>

          <el-form-item label="艺术风格" prop="art_style">
            <el-input v-model="projectForm.art_style" />
          </el-form-item>

          <el-form-item label="画幅比例" prop="video_ratio">
            <el-select v-model="projectForm.video_ratio">
              <el-option label="9:16" value="9:16" />
              <el-option label="16:9" value="16:9" />
              <el-option label="1:1" value="1:1" />
            </el-select>
          </el-form-item>

          <el-form-item label="图像模型" prop="image_model">
            <el-input v-model="projectForm.image_model" />
          </el-form-item>

          <el-form-item label="视频模型" prop="video_model">
            <el-input v-model="projectForm.video_model" />
          </el-form-item>

          <el-form-item label="图像质量" prop="image_quality">
            <el-select v-model="projectForm.image_quality">
              <el-option label="standard" value="standard" />
              <el-option label="hd" value="hd" />
              <el-option label="high" value="high" />
            </el-select>
          </el-form-item>

          <el-form-item label="生成模式" prop="mode">
            <el-select v-model="projectForm.mode">
              <el-option label="纯文本生成视频" value="text" />
              <el-option label="单图参考" value="singleImage" />
              <el-option label="必须首尾帧" value="startEndRequired" />
              <el-option label="尾帧可选" value="endFrameOptional" />
              <el-option label="首帧可选" value="startFrameOptional" />
            </el-select>
          </el-form-item>
        </div>

        <el-form-item label="导演手册" prop="director_manual">
          <el-input v-model="projectForm.director_manual" maxlength="4000" rows="5" show-word-limit type="textarea" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="projectDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="projectSubmitting" @click="submitProject">
          保存
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="memberDialogVisible"
      :title="memberDialogTitle"
      width="760px"
      destroy-on-close
    >
      <section class="member-search">
        <el-input
          v-model="candidateKeyword"
          clearable
          placeholder="输入用户名或邮箱搜索可邀请成员"
          @keyup.enter="searchCandidates"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="inviteRole" class="role-select">
          <el-option label="管理员" value="admin" />
          <el-option label="管理者" value="manager" />
          <el-option label="编辑者" value="editor" />
          <el-option label="查看者" value="viewer" />
        </el-select>
        <el-button :loading="candidatesLoading" @click="searchCandidates">搜索</el-button>
      </section>

      <el-table
        v-if="candidates.length > 0"
        :data="candidates"
        class="candidate-table"
        size="small"
      >
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="nickname" label="昵称" min-width="120" />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column label="操作" width="100" align="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="inviteCandidate(row)">邀请</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-divider />

      <el-table
        v-loading="membersLoading"
        :data="members"
        element-loading-background="rgba(13, 17, 23, 0.55)"
        size="small"
      >
        <el-table-column prop="user_public_id" label="成员 ID" min-width="240" />
        <el-table-column label="角色" width="160">
          <template #default="{ row }">
            <el-select
              v-model="row.role"
              :disabled="row.role === 'owner'"
              size="small"
              @change="updateMemberRole(row)"
            >
              <el-option label="所有者" value="owner" disabled />
              <el-option label="管理员" value="admin" />
              <el-option label="管理者" value="manager" />
              <el-option label="编辑者" value="editor" />
              <el-option label="查看者" value="viewer" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="加入时间" width="170">
          <template #default="{ row }">{{ formatDate(row.joined_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" align="right">
          <template #default="{ row }">
            <el-button
              :disabled="row.role === 'owner'"
              type="danger"
              link
              @click="removeMember(row)"
            >
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { AxiosError } from 'axios'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Connection,
  Delete,
  Document,
  EditPen,
  Folder,
  List,
  Plus,
  Search,
  Setting,
  SwitchButton,
  UserFilled,
} from '@element-plus/icons-vue'
import {
  createProjectApi,
  deleteProjectApi,
  disableProjectApi,
  enableProjectApi,
  inviteProjectMemberApi,
  listProjectMembersApi,
  listProjectsApi,
  removeProjectMemberApi,
  searchProjectMemberCandidatesApi,
  searchProjectsByNameApi,
  updateProjectApi,
  updateProjectMemberRoleApi,
  type ProjectMemberRecord,
  type ProjectMemberRole,
  type ProjectPayload,
  type ProjectRecord,
  type ProjectVideoMode,
  type UserRecord,
} from '@/api/project'

type ProjectDialogMode = 'create' | 'edit'

const router = useRouter()
const projectFormRef = ref<FormInstance>()

const loading = ref(false)
const projectSubmitting = ref(false)
const projects = ref<ProjectRecord[]>([])
const currentPage = ref(1)
const pageSize = ref(4)
const searchKeyword = ref('')

const projectDialogVisible = ref(false)
const projectDialogMode = ref<ProjectDialogMode>('create')
const editingProjectPublicId = ref('')

const memberDialogVisible = ref(false)
const memberProject = ref<ProjectRecord | null>(null)
const members = ref<ProjectMemberRecord[]>([])
const membersLoading = ref(false)
const candidateKeyword = ref('')
const candidates = ref<UserRecord[]>([])
const candidatesLoading = ref(false)
const inviteRole = ref<ProjectMemberRole>('editor')

const projectForm = reactive<ProjectPayload>({
  name: '',
  intro: '',
  project_type: 'novel_to_video',
  content_type: 'novel',
  art_style: '3D_chinese_traditional',
  director_manual: '',
  video_ratio: '9:16',
  image_model: '',
  video_model: '',
  image_quality: 'standard',
  mode: 'text',
})

const projectRules: FormRules<ProjectPayload> = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
}

const pagedProjects = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return projects.value.slice(start, start + pageSize.value)
})

const projectDialogTitle = computed(() => (projectDialogMode.value === 'create' ? '新建项目' : '编辑项目'))
const memberDialogTitle = computed(() => (memberProject.value ? `成员管理：${memberProject.value.name}` : '成员管理'))

const loadProjects = async () => {
  loading.value = true
  try {
    const { data } = await listProjectsApi()
    projects.value = data
    currentPage.value = 1
    searchKeyword.value = ''
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  } finally {
    loading.value = false
  }
}

const handleSearch = async () => {
  const keyword = searchKeyword.value.trim()
  if (!keyword) {
    await loadProjects()
    return
  }

  loading.value = true
  try {
    const { data } = await searchProjectsByNameApi(keyword)
    projects.value = data
    currentPage.value = 1
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  projectDialogMode.value = 'create'
  editingProjectPublicId.value = ''
  resetProjectForm()
  projectDialogVisible.value = true
}

const openEditDialog = (project: ProjectRecord) => {
  projectDialogMode.value = 'edit'
  editingProjectPublicId.value = project.public_id
  Object.assign(projectForm, pickProjectPayload(project))
  projectDialogVisible.value = true
}

const submitProject = async () => {
  if (!projectFormRef.value) return
  const valid = await projectFormRef.value.validate().catch(() => false)
  if (!valid) return

  projectSubmitting.value = true
  try {
    if (projectDialogMode.value === 'create') {
      await createProjectApi({ ...projectForm })
      ElMessage.success('项目已创建')
    } else {
      await updateProjectApi(editingProjectPublicId.value, { ...projectForm })
      ElMessage.success('项目已更新')
    }
    projectDialogVisible.value = false
    await refreshAfterMutation()
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  } finally {
    projectSubmitting.value = false
  }
}

const toggleProjectStatus = async (project: ProjectRecord) => {
  try {
    if (project.disabled_at) {
      await enableProjectApi(project.public_id)
      ElMessage.success('项目已启用')
    } else {
      await disableProjectApi(project.public_id)
      ElMessage.success('项目已禁用')
    }
    await refreshAfterMutation()
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  }
}

const handleDeleteProject = async (project: ProjectRecord) => {
  try {
    await ElMessageBox.confirm(`确定删除项目“${project.name}”吗？删除后不可恢复。`, '删除项目', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger',
    })

    await deleteProjectApi(project.public_id)
    ElMessage.success('项目已删除')
    await refreshAfterMutation()
  } catch (error) {
    if (isCancelError(error)) return
    ElMessage.error(getErrorMessage(error))
  }
}

const openMemberDialog = async (project: ProjectRecord) => {
  memberProject.value = project
  members.value = []
  candidates.value = []
  candidateKeyword.value = ''
  inviteRole.value = 'editor'
  memberDialogVisible.value = true
  await loadMembers()
}

const loadMembers = async () => {
  if (!memberProject.value) return
  membersLoading.value = true
  try {
    const { data } = await listProjectMembersApi(memberProject.value.public_id)
    members.value = data
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  } finally {
    membersLoading.value = false
  }
}

const searchCandidates = async () => {
  if (!memberProject.value) return
  const keyword = candidateKeyword.value.trim()
  if (!keyword) {
    candidates.value = []
    return
  }

  candidatesLoading.value = true
  try {
    const { data } = await searchProjectMemberCandidatesApi(memberProject.value.public_id, keyword)
    candidates.value = data
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  } finally {
    candidatesLoading.value = false
  }
}

const inviteCandidate = async (candidate: UserRecord) => {
  if (!memberProject.value) return
  try {
    await inviteProjectMemberApi(memberProject.value.public_id, {
      user_public_id: candidate.public_id,
      role: inviteRole.value,
    })
    ElMessage.success('成员已邀请')
    candidates.value = candidates.value.filter((item) => item.public_id !== candidate.public_id)
    await loadMembers()
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  }
}

const updateMemberRole = async (member: ProjectMemberRecord) => {
  if (!memberProject.value || member.role === 'owner') return
  try {
    await updateProjectMemberRoleApi(memberProject.value.public_id, member.user_public_id, member.role)
    ElMessage.success('成员角色已更新')
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
    await loadMembers()
  }
}

const removeMember = async (member: ProjectMemberRecord) => {
  if (!memberProject.value || member.role === 'owner') return
  try {
    await ElMessageBox.confirm('确定移除该项目成员吗？', '移除成员', {
      confirmButtonText: '移除',
      cancelButtonText: '取消',
      type: 'warning',
      confirmButtonClass: 'el-button--danger',
    })
    await removeProjectMemberApi(memberProject.value.public_id, member.user_public_id)
    ElMessage.success('成员已移除')
    await loadMembers()
  } catch (error) {
    if (isCancelError(error)) return
    ElMessage.error(getErrorMessage(error))
  }
}

const refreshAfterMutation = async () => {
  if (searchKeyword.value.trim()) {
    await handleSearch()
  } else {
    await loadProjects()
  }
}

const resetProjectForm = () => {
  Object.assign(projectForm, {
    name: '',
    intro: '',
    project_type: 'novel_to_video',
    content_type: 'novel',
    art_style: '3D_chinese_traditional',
    director_manual: '',
    video_ratio: '9:16',
    image_model: '',
    video_model: '',
    image_quality: 'standard',
    mode: 'text' as ProjectVideoMode,
  })
}

const pickProjectPayload = (project: ProjectRecord): ProjectPayload => ({
  name: project.name,
  intro: project.intro,
  project_type: project.project_type,
  content_type: project.content_type,
  art_style: project.art_style,
  director_manual: project.director_manual,
  video_ratio: project.video_ratio,
  image_model: project.image_model,
  video_model: project.video_model,
  image_quality: project.image_quality,
  mode: project.mode,
})

const contentTypeLabel = (contentType: string) => {
  const labels: Record<string, string> = {
    novel: '小说',
    script: '剧本',
    original: '原创',
  }
  return labels[contentType] ?? contentType
}

const formatDate = (value: string) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (num: number) => String(num).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

const getErrorMessage = (error: unknown) => {
  const axiosError = error as AxiosError<{ detail?: string }>
  return axiosError.response?.data?.detail || axiosError.message || '请求失败'
}

const isCancelError = (error: unknown) => error === 'cancel' || error === 'close'

const goHome = () => {
  router.push('/project')
}

const showComingSoon = () => {
  ElMessage.info('功能开发中')
}

onMounted(loadProjects)
</script>

<style scoped>
.project-page {
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
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.45),
    0 10px 24px rgba(243, 217, 107, 0.28);
}

.brand:active {
  transform: translateY(0) scale(0.97);
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

.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.search-input {
  max-width: 420px;
}

.create-button {
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

.create-button :deep(.el-icon) {
  margin-right: 0;
  font-size: 16px;
}

.create-button:hover,
.create-button:focus {
  background: #1d4ed8;
  box-shadow: 0 14px 30px rgba(37, 99, 235, 0.28);
  transform: translateY(-1px);
}

.create-button:active {
  transform: translateY(0);
}

.project-grid {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(2, minmax(320px, 1fr));
  gap: 16px 18px;
  align-content: start;
  padding-right: 6px;
}

.empty-state {
  grid-column: 1 / -1;
  align-self: center;
}

.project-card {
  display: flex;
  flex-direction: column;
  border-radius: 16px;
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
  padding: 18px 22px 0;
  border-bottom: 0;
}

.project-card :deep(.el-card__body) {
  display: flex;
  flex: 1;
  flex-direction: column;
  padding: 10px 22px 16px;
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
  font-size: 18px;
  font-weight: 700;
  line-height: 1.25;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.source-tag {
  height: 26px;
  padding: 0 10px;
  color: #d1d5db;
  font-size: 12px;
  font-weight: 500;
  border-color: rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.05);
  white-space: nowrap;
}

.model-tag,
.ratio-tag {
  width: fit-content;
  height: 24px;
  padding: 0 10px;
  font-size: 11px;
  font-weight: 500;
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
}

.model-tag {
  color: #c7d2fe;
  border-color: rgba(37, 99, 235, 0.22);
  background: rgba(37, 99, 235, 0.12);
}

.ratio-tag {
  color: #bae6fd;
  border-color: rgba(14, 165, 233, 0.22);
  background: rgba(14, 165, 233, 0.1);
}

.summary {
  flex: 1;
  margin: 10px 0 0;
  color: #b8c2cc;
  font-size: 13px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 14px;
}

.time {
  color: #8b949e;
  font-size: 12px;
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
  font-variant-numeric: tabular-nums;
}

.actions {
  display: flex;
  align-items: center;
  gap: 8px;
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
  font-variant-numeric: tabular-nums;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.02);
  transition: color 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.pagination-wrap :deep(.el-pagination.is-background .el-pager li:hover) {
  color: #e6edf3;
  border-color: rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.05);
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
  font-variant-numeric: tabular-nums;
}

.project-form {
  padding-right: 8px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 12px;
}

.member-search {
  display: grid;
  grid-template-columns: 1fr 140px auto;
  gap: 10px;
  align-items: center;
}

.candidate-table {
  margin-top: 12px;
}

.role-select {
  width: 140px;
}

@media (max-width: 860px) {
  .title {
    font-size: 28px;
  }

  .project-grid,
  .form-grid {
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
    height: calc(100vh - 28px);
    height: calc(100dvh - 28px);
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
    padding: 18px 16px 16px;
  }

  .page-header,
  .toolbar,
  .card-head,
  .card-footer,
  .member-search {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar,
  .member-search {
    display: flex;
  }

  .title {
    font-size: 26px;
  }

  .desc {
    font-size: 13px;
  }

  .create-button {
    align-self: flex-start;
  }

  .search-input,
  .role-select {
    max-width: none;
    width: 100%;
  }

  .project-card :deep(.el-card__header) {
    padding: 16px 18px 0;
  }

  .project-card :deep(.el-card__body) {
    padding: 10px 18px 14px;
  }
}
</style>