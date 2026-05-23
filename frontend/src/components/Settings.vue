<template>
  <el-dialog
    v-model="visible"
    title="设置"
    width="860px"
    top="8vh"
    destroy-on-close
    class="settings-dark-dialog"
  >
    <div class="settings-shell">
      <aside class="settings-nav">
        <button
          v-for="item in categories"
          :key="item.key"
          class="settings-nav__btn"
          :class="{ 'is-active': activeKey === item.key }"
          @click="activeKey = item.key"
        >
          <el-icon class="settings-nav__icon"><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </button>
      </aside>

      <section class="settings-panel">
        <!-- 用户信息更新 -->
        <div v-if="activeKey === 'profile'" class="settings-section">
          <header class="section-head">
            <h2>个人资料</h2>
            <p>修改账号显示名称、邮箱和昵称</p>
          </header>

          <el-form
            ref="profileFormRef"
            v-loading="profileLoading"
            :model="profileForm"
            :rules="profileRules"
            label-position="top"
            class="settings-form"
            element-loading-background="rgba(13, 17, 23, 0.55)"
          >
            <div class="account-grid">
              <div class="account-avatar">
                <div class="avatar-circle">
                  <img v-if="profileForm.avatar_url" :src="profileForm.avatar_url" class="avatar-image" :alt="avatarLetter" />
                  <template v-else>{{ avatarLetter }}</template>
                </div>
                <el-button class="ghost-btn" size="small" :loading="avatarUploading" @click="pickAvatarFile">更换头像</el-button>
                <input
                  ref="avatarInputRef"
                  type="file"
                  accept="image/png,image/jpeg,image/jpg"
                  hidden
                  @change="onAvatarFileSelected"
                />
              </div>

              <div class="account-fields">
                <el-form-item label="账号" prop="username">
                  <el-input v-model="profileForm.username" placeholder="登录账号" maxlength="32" />
                </el-form-item>
                <el-form-item label="昵称" prop="nickname">
                  <el-input v-model="profileForm.nickname" placeholder="显示名称" maxlength="32" />
                </el-form-item>
                <el-form-item label="邮箱" prop="email">
                  <el-input v-model="profileForm.email" placeholder="example@mail.com" />
                </el-form-item>
              </div>
            </div>

            <div class="settings-form__actions">
              <el-button class="ghost-btn" @click="resetProfile">重置</el-button>
              <el-button type="primary" :loading="profileSaving" @click="saveProfile">保存修改</el-button>
            </div>
          </el-form>
        </div>

        <!-- 密码修改 -->
        <div v-else-if="activeKey === 'password'" class="settings-section">
          <header class="section-head">
            <h2>修改密码</h2>
            <p>定期更换密码，保障账号安全</p>
          </header>

          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-position="top"
            class="settings-form password-form"
          >
            <el-form-item label="当前密码" prop="oldPassword">
              <el-input
                v-model="passwordForm.oldPassword"
                type="password"
                show-password
                placeholder="输入当前登录密码"
              />
            </el-form-item>

            <el-form-item label="新密码" prop="newPassword">
              <el-input
                v-model="passwordForm.newPassword"
                type="password"
                show-password
                placeholder="8 位以上，建议含大小写字母与数字"
              />
              <div class="password-strength">
                <div
                  v-for="i in 4"
                  :key="i"
                  class="password-strength__bar"
                  :class="{ 'is-on': passwordStrength >= i }"
                  :data-level="passwordStrength"
                ></div>
                <span class="password-strength__label">{{ passwordStrengthLabel }}</span>
              </div>
            </el-form-item>

            <el-form-item label="确认新密码" prop="confirmPassword">
              <el-input
                v-model="passwordForm.confirmPassword"
                type="password"
                show-password
                placeholder="再次输入新密码"
              />
            </el-form-item>

            <div class="settings-form__actions">
              <el-button class="ghost-btn" @click="resetPassword">清空</el-button>
              <el-button type="primary" :loading="passwordSaving" @click="savePassword">提交修改</el-button>
            </div>
          </el-form>
        </div>

        <!-- 注销登录 -->
        <div v-else-if="activeKey === 'logout'" class="settings-section">
          <header class="section-head">
            <h2>注销登录</h2>
            <p>退出当前账号，需要重新登录后才能继续使用</p>
          </header>

          <div class="logout-card">
            <div class="logout-card__main">
              <div class="logout-card__avatar">
                <img
                  v-if="profileForm.avatar_url"
                  :src="profileForm.avatar_url"
                  class="logout-card__avatar-image"
                  :alt="avatarLetter"
                />
                <template v-else>{{ avatarLetter }}</template>
              </div>
              <div class="logout-card__info">
                <div class="logout-card__name">{{ profileForm.nickname || profileForm.username }}</div>
                <div class="logout-card__sub">{{ profileForm.username }} · {{ profileForm.email || '未填写邮箱' }}</div>
                <div class="logout-card__meta">
                  <span class="logout-tag">最近登录：{{ lastLoginAt }}</span>
                  <span class="logout-tag">设备：{{ currentDevice }}</span>
                </div>
              </div>
            </div>

            <div class="logout-card__tip">
              <el-icon><WarningFilled /></el-icon>
              <span>注销后将清除本地登录凭证，需要重新输入账号密码登录。</span>
            </div>

            <div class="logout-actions">
              <el-button class="ghost-btn" @click="visible = false">取消</el-button>
              <el-button type="danger" :loading="loggingOut" @click="logout">
                <el-icon><SwitchButton /></el-icon>
                确认注销登录
              </el-button>
            </div>
          </div>
        </div>
      </section>
    </div>

    <el-dialog
      v-model="cropDialogVisible"
      title="裁剪头像"
      width="520px"
      append-to-body
      destroy-on-close
      class="settings-dark-dialog"
      @closed="onCropDialogClosed"
    >
      <div class="avatar-cropper">
        <div
          ref="cropStageRef"
          class="avatar-cropper__stage"
          :style="stageStyle"
        >
          <img
            v-if="cropSourceUrl"
            :src="cropSourceUrl"
            class="avatar-cropper__image"
            :style="imageStyle"
            draggable="false"
            alt="裁剪原图"
          />
          <div
            v-if="cropBox.size > 0"
            class="avatar-cropper__box"
            :style="boxStyle"
            @pointerdown.stop="onBoxPointerDown"
          >
            <span class="avatar-cropper__grid"></span>
            <span
              class="avatar-cropper__handle"
              @pointerdown.stop="onHandlePointerDown"
            ></span>
          </div>
        </div>
        <p class="avatar-cropper__hint">拖动选区移动位置；右下角可缩放。选区将作为 1:1 头像。</p>
      </div>

      <template #footer>
        <el-button class="ghost-btn" @click="cropDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="avatarUploading" @click="confirmCrop">确认裁剪并上传</el-button>
      </template>
    </el-dialog>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { AxiosError } from 'axios'
import type { FormInstance, FormRules, FormItemRule } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Lock, SwitchButton, User, WarningFilled } from '@element-plus/icons-vue'
import {
  getCurrentUserApi,
  updateCurrentUserPasswordApi,
  updateCurrentUserProfileApi,
  uploadCurrentUserAvatarApi,
  type UserRecord,
} from '../api/user'

const visible = defineModel<boolean>({ default: false })
const router = useRouter()

type CategoryKey = 'profile' | 'password' | 'logout'

const categories: { key: CategoryKey; label: string; icon: any }[] = [
  { key: 'profile', label: '个人资料', icon: User },
  { key: 'password', label: '修改密码', icon: Lock },
  { key: 'logout', label: '注销登录', icon: SwitchButton },
]

const activeKey = ref<CategoryKey>('profile')

interface ProfileFormState {
  username: string
  nickname: string
  email: string
  avatar_url: string
  last_login_at: string | null
}

const emptyProfile = (): ProfileFormState => ({
  username: '',
  nickname: '',
  email: '',
  avatar_url: '',
  last_login_at: null,
})

const currentUserSnapshot = ref<ProfileFormState>(emptyProfile())

// ---------- 个人资料 ----------
const profileFormRef = ref<FormInstance>()
const profileLoading = ref(false)
const profileSaving = ref(false)
const profileForm = reactive<ProfileFormState>(emptyProfile())

const profileRules: FormRules<ProfileFormState> = {
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 3, max: 32, message: '账号长度需在 3-32 之间', trigger: 'blur' },
  ],
  nickname: [{ max: 32, message: '昵称不能超过 32 字', trigger: 'blur' }],
  email: [
    {
      pattern: /^[\w.+-]+@[\w-]+\.[\w.-]+$/,
      message: '请输入有效的邮箱地址',
      trigger: 'blur',
    },
  ],
}

const avatarLetter = computed(() => (profileForm.nickname || profileForm.username || 'A').slice(0, 1).toUpperCase())

const getErrorMessage = (error: unknown) => {
  const axiosError = error as AxiosError<{ detail?: string }>
  return axiosError.response?.data?.detail || axiosError.message || '请求失败'
}

const applyUser = (user: UserRecord) => {
  const next: ProfileFormState = {
    username: user.username ?? '',
    nickname: user.nickname ?? '',
    email: user.email ?? '',
    avatar_url: user.avatar_url ?? '',
    last_login_at: user.last_login_at,
  }
  Object.assign(profileForm, next)
  currentUserSnapshot.value = { ...next }
}

const loadCurrentUser = async () => {
  profileLoading.value = true
  try {
    const { data } = await getCurrentUserApi()
    applyUser(data)
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  } finally {
    profileLoading.value = false
  }
}

const resetProfile = () => {
  Object.assign(profileForm, currentUserSnapshot.value)
  profileFormRef.value?.clearValidate()
  ElMessage.info('已恢复修改前的资料')
}

const saveProfile = async () => {
  if (!profileFormRef.value) return
  const valid = await profileFormRef.value.validate().catch(() => false)
  if (!valid) return

  profileSaving.value = true
  try {
    const { data } = await updateCurrentUserProfileApi({
      username: profileForm.username,
      nickname: profileForm.nickname || null,
      email: profileForm.email || null,
    })
    applyUser(data)
    ElMessage.success('个人资料已保存')
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  } finally {
    profileSaving.value = false
  }
}

const avatarInputRef = ref<HTMLInputElement | null>(null)
const avatarUploading = ref(false)
const ALLOWED_AVATAR_TYPES = ['image/png', 'image/jpeg', 'image/jpg']
const MAX_AVATAR_BYTES = 5 * 1024 * 1024

const pickAvatarFile = () => {
  if (avatarUploading.value) return
  avatarInputRef.value?.click()
}

const onAvatarFileSelected = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  target.value = ''
  if (!file) return

  if (!ALLOWED_AVATAR_TYPES.includes(file.type)) {
    ElMessage.error('仅支持 PNG/JPEG/JPG 格式的图片')
    return
  }
  if (file.size > MAX_AVATAR_BYTES) {
    ElMessage.error('图片过大，最多支持 5MB')
    return
  }
  openCropper(file)
}

// ---------- 头像裁剪 ----------
const CROP_STAGE_MAX = 420
const CROP_MIN_SIZE = 48

const cropDialogVisible = ref(false)
const cropSourceFile = ref<File | null>(null)
const cropSourceUrl = ref('')
const cropStageRef = ref<HTMLDivElement | null>(null)
const cropImageNatural = reactive({ width: 0, height: 0 })
const cropImageDisplay = reactive({ width: 0, height: 0 })
const cropBox = reactive({ x: 0, y: 0, size: 0 })

let cropDragMode: 'move' | 'resize' | null = null
let cropDragStart = { pointerX: 0, pointerY: 0, boxX: 0, boxY: 0, boxSize: 0 }

const stageStyle = computed(() => ({
  width: cropImageDisplay.width ? `${cropImageDisplay.width}px` : '320px',
  height: cropImageDisplay.height ? `${cropImageDisplay.height}px` : '320px',
}))

const imageStyle = computed(() => ({
  width: `${cropImageDisplay.width}px`,
  height: `${cropImageDisplay.height}px`,
}))

const boxStyle = computed(() => ({
  left: `${cropBox.x}px`,
  top: `${cropBox.y}px`,
  width: `${cropBox.size}px`,
  height: `${cropBox.size}px`,
}))

const openCropper = (file: File) => {
  cropSourceFile.value = file
  if (cropSourceUrl.value) URL.revokeObjectURL(cropSourceUrl.value)
  cropSourceUrl.value = URL.createObjectURL(file)
  cropBox.size = 0
  cropDialogVisible.value = true

  const img = new Image()
  img.onload = () => {
    cropImageNatural.width = img.naturalWidth
    cropImageNatural.height = img.naturalHeight
    const fit = Math.min(
      CROP_STAGE_MAX / img.naturalWidth,
      CROP_STAGE_MAX / img.naturalHeight,
      1,
    )
    cropImageDisplay.width = Math.max(1, Math.round(img.naturalWidth * fit))
    cropImageDisplay.height = Math.max(1, Math.round(img.naturalHeight * fit))
    const side = Math.min(cropImageDisplay.width, cropImageDisplay.height)
    cropBox.size = side
    cropBox.x = Math.round((cropImageDisplay.width - side) / 2)
    cropBox.y = Math.round((cropImageDisplay.height - side) / 2)
  }
  img.onerror = () => {
    ElMessage.error('图片加载失败')
    cropDialogVisible.value = false
  }
  img.src = cropSourceUrl.value
}

const onCropDialogClosed = () => {
  if (cropSourceUrl.value) URL.revokeObjectURL(cropSourceUrl.value)
  cropSourceUrl.value = ''
  cropSourceFile.value = null
  cropImageNatural.width = 0
  cropImageNatural.height = 0
  cropImageDisplay.width = 0
  cropImageDisplay.height = 0
  cropBox.size = 0
  detachCropPointerListeners()
}

const onBoxPointerDown = (event: PointerEvent) => {
  cropDragMode = 'move'
  cropDragStart = {
    pointerX: event.clientX,
    pointerY: event.clientY,
    boxX: cropBox.x,
    boxY: cropBox.y,
    boxSize: cropBox.size,
  }
  attachCropPointerListeners()
}

const onHandlePointerDown = (event: PointerEvent) => {
  cropDragMode = 'resize'
  cropDragStart = {
    pointerX: event.clientX,
    pointerY: event.clientY,
    boxX: cropBox.x,
    boxY: cropBox.y,
    boxSize: cropBox.size,
  }
  attachCropPointerListeners()
}

const onCropPointerMove = (event: PointerEvent) => {
  if (!cropDragMode) return
  const dx = event.clientX - cropDragStart.pointerX
  const dy = event.clientY - cropDragStart.pointerY

  if (cropDragMode === 'move') {
    const maxX = cropImageDisplay.width - cropBox.size
    const maxY = cropImageDisplay.height - cropBox.size
    cropBox.x = Math.max(0, Math.min(cropDragStart.boxX + dx, maxX))
    cropBox.y = Math.max(0, Math.min(cropDragStart.boxY + dy, maxY))
    return
  }

  const delta = Math.max(dx, dy)
  const maxBySpace = Math.min(
    cropImageDisplay.width - cropDragStart.boxX,
    cropImageDisplay.height - cropDragStart.boxY,
  )
  cropBox.size = Math.max(
    CROP_MIN_SIZE,
    Math.min(cropDragStart.boxSize + delta, maxBySpace),
  )
}

const onCropPointerUp = () => {
  cropDragMode = null
  detachCropPointerListeners()
}

const attachCropPointerListeners = () => {
  document.addEventListener('pointermove', onCropPointerMove)
  document.addEventListener('pointerup', onCropPointerUp)
  document.addEventListener('pointercancel', onCropPointerUp)
}

const detachCropPointerListeners = () => {
  document.removeEventListener('pointermove', onCropPointerMove)
  document.removeEventListener('pointerup', onCropPointerUp)
  document.removeEventListener('pointercancel', onCropPointerUp)
}

const renderCropBlob = (sx: number, sy: number, ss: number): Promise<Blob | null> => {
  return new Promise((resolve) => {
    if (!cropSourceUrl.value) return resolve(null)
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      canvas.width = ss
      canvas.height = ss
      const ctx = canvas.getContext('2d')
      if (!ctx) return resolve(null)
      ctx.drawImage(img, sx, sy, ss, ss, 0, 0, ss, ss)
      canvas.toBlob((blob) => resolve(blob), 'image/jpeg', 0.92)
    }
    img.onerror = () => resolve(null)
    img.src = cropSourceUrl.value
  })
}

const confirmCrop = async () => {
  if (!cropSourceFile.value || cropBox.size === 0 || !cropImageDisplay.width) return
  const ratio = cropImageNatural.width / cropImageDisplay.width
  const sx = Math.round(cropBox.x * ratio)
  const sy = Math.round(cropBox.y * ratio)
  const ss = Math.max(1, Math.round(cropBox.size * ratio))

  avatarUploading.value = true
  try {
    const blob = await renderCropBlob(sx, sy, ss)
    if (!blob) {
      ElMessage.error('裁剪失败，请重试')
      return
    }
    const file = new File([blob], 'avatar.jpg', { type: 'image/jpeg' })
    const { data } = await uploadCurrentUserAvatarApi(file)
    applyUser(data)
    ElMessage.success('头像已更新')
    cropDialogVisible.value = false
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  } finally {
    avatarUploading.value = false
  }
}

// ---------- 修改密码 ----------
const passwordFormRef = ref<FormInstance>()
const passwordSaving = ref(false)
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const validateNewPassword: FormItemRule['validator'] = (_rule, value, cb) => {
  if (!value) return cb(new Error('请输入新密码'))
  if (value.length < 8) return cb(new Error('新密码长度不少于 8 位'))
  if (value === passwordForm.oldPassword) return cb(new Error('新密码不能与当前密码相同'))
  cb()
}

const validateConfirmPassword: FormItemRule['validator'] = (_rule, value, cb) => {
  if (!value) return cb(new Error('请再次输入新密码'))
  if (value !== passwordForm.newPassword) return cb(new Error('两次输入的密码不一致'))
  cb()
}

const passwordRules: FormRules<typeof passwordForm> = {
  oldPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [{ required: true, validator: validateNewPassword, trigger: 'blur' }],
  confirmPassword: [{ required: true, validator: validateConfirmPassword, trigger: 'blur' }],
}

const passwordStrength = computed(() => {
  const value = passwordForm.newPassword
  if (!value) return 0
  let score = 0
  if (value.length >= 8) score += 1
  if (/[a-z]/.test(value) && /[A-Z]/.test(value)) score += 1
  if (/\d/.test(value)) score += 1
  if (/[^A-Za-z0-9]/.test(value)) score += 1
  return score
})

const passwordStrengthLabel = computed(() => {
  if (!passwordForm.newPassword) return '请输入密码'
  return ['极弱', '较弱', '一般', '强', '极强'][passwordStrength.value] || '极弱'
})

watch(
  () => passwordForm.newPassword,
  () => {
    if (passwordForm.confirmPassword) {
      passwordFormRef.value?.validateField('confirmPassword').catch(() => {})
    }
  },
)

const resetPassword = () => {
  passwordForm.oldPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  passwordFormRef.value?.clearValidate()
}

const savePassword = async () => {
  if (!passwordFormRef.value) return
  const valid = await passwordFormRef.value.validate().catch(() => false)
  if (!valid) return

  passwordSaving.value = true
  try {
    await updateCurrentUserPasswordApi({
      old_password: passwordForm.oldPassword,
      new_password: passwordForm.newPassword,
      confirm_password: passwordForm.confirmPassword,
    })
    resetPassword()
    ElMessage.success('密码修改成功，下次登录请使用新密码')
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  } finally {
    passwordSaving.value = false
  }
}

// ---------- 注销登录 ----------
const loggingOut = ref(false)

const formatDateTime = (value: string | null) => {
  if (!value) return '暂无记录'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const pad = (num: number) => String(num).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

const lastLoginAt = computed(() => formatDateTime(profileForm.last_login_at))

const currentDevice = computed(() => {
  if (typeof navigator === 'undefined') return '未知设备'
  return navigator.userAgent || '未知设备'
})

const logout = async () => {
  try {
    await ElMessageBox.confirm('确认要退出当前账号吗？', '注销登录', {
      confirmButtonText: '确认注销',
      cancelButtonText: '再想想',
      type: 'warning',
      confirmButtonClass: 'el-button--danger',
      customClass: 'settings-dark-messagebox',
    })
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    return
  }

  loggingOut.value = true
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('token_type')
  localStorage.removeItem('expires_in')
  localStorage.removeItem('user')
  loggingOut.value = false
  visible.value = false
  ElMessage.success('已注销，正在返回登录页')
  router.push('/login')
}

// 弹窗每次打开复位到第一项 + 清空密码字段 + 加载当前用户
watch(visible, (val) => {
  if (val) {
    activeKey.value = 'profile'
    resetPassword()
    void loadCurrentUser()
  }
})
</script>

<style scoped>
.settings-shell {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 18px;
  min-height: 460px;
}

.settings-nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 6px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.02);
  align-self: flex-start;
}

.settings-nav__btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: 1px solid transparent;
  border-radius: 10px;
  background: transparent;
  color: #c5cdd6;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  transition: background-color 0.18s ease, color 0.18s ease, border-color 0.18s ease;
}

.settings-nav__btn:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #ffffff;
}

.settings-nav__btn.is-active {
  color: #dbeafe;
  border-color: rgba(37, 99, 235, 0.32);
  background: linear-gradient(180deg, rgba(37, 99, 235, 0.22), rgba(37, 99, 235, 0.1));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.settings-nav__icon {
  font-size: 18px;
}

.settings-panel {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.settings-section {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.section-head h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #f2f4f8;
}

.section-head p {
  margin: 4px 0 0;
  color: #8b949e;
  font-size: 13px;
}

.settings-form__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.ghost-btn {
  background-color: rgba(255, 255, 255, 0.04) !important;
  border-color: rgba(255, 255, 255, 0.12) !important;
  color: #e6edf3 !important;
  border-radius: 10px !important;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.ghost-btn:hover {
  background-color: rgba(255, 255, 255, 0.08) !important;
  border-color: rgba(255, 255, 255, 0.22) !important;
  color: #ffffff !important;
}

/* 个人资料 */
.account-grid {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 24px;
  align-items: flex-start;
}

.account-avatar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.avatar-circle {
  width: 96px;
  height: 96px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  font-size: 36px;
  font-weight: 800;
  color: #0a0a0a;
  background: linear-gradient(135deg, #f3d96b, #c4b5fd);
  box-shadow: 0 12px 24px rgba(243, 217, 107, 0.18);
  user-select: none;
  overflow: hidden;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* 头像裁剪 */
.avatar-cropper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.avatar-cropper__stage {
  position: relative;
  display: inline-block;
  max-width: 100%;
  background: #0c1015;
  border-radius: 12px;
  overflow: hidden;
  touch-action: none;
  user-select: none;
}

.avatar-cropper__image {
  display: block;
  pointer-events: none;
  user-select: none;
  -webkit-user-drag: none;
}

.avatar-cropper__box {
  position: absolute;
  box-sizing: border-box;
  border: 2px solid #ffffff;
  border-radius: 4px;
  box-shadow: 0 0 0 9999px rgba(7, 10, 16, 0.55);
  cursor: move;
  touch-action: none;
}

.avatar-cropper__grid {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    linear-gradient(to right, rgba(255, 255, 255, 0.35) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(255, 255, 255, 0.35) 1px, transparent 1px);
  background-size: 33.333% 33.333%;
  background-position: 0 0;
}

.avatar-cropper__handle {
  position: absolute;
  right: -7px;
  bottom: -7px;
  width: 14px;
  height: 14px;
  border-radius: 3px;
  background: #ffffff;
  border: 1.5px solid rgba(37, 99, 235, 0.6);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
  cursor: nwse-resize;
  touch-action: none;
}

.avatar-cropper__hint {
  margin: 0;
  color: #8b949e;
  font-size: 12px;
}

.account-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 18px;
}

/* 密码 */
.password-form {
  max-width: 480px;
}

.password-strength {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.password-strength__bar {
  width: 48px;
  height: 4px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  transition: background 0.2s ease;
}

.password-strength__bar.is-on[data-level='1'] {
  background: #f87171;
}

.password-strength__bar.is-on[data-level='2'] {
  background: #fb923c;
}

.password-strength__bar.is-on[data-level='3'] {
  background: #facc15;
}

.password-strength__bar.is-on[data-level='4'] {
  background: #22c55e;
}

.password-strength__label {
  margin-left: 8px;
  font-size: 12px;
  color: #8b949e;
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
}

/* 注销 */
.logout-card {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 20px 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.022), rgba(255, 255, 255, 0.012));
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.logout-card__main {
  display: flex;
  align-items: center;
  gap: 18px;
}

.logout-card__avatar {
  width: 64px;
  height: 64px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  font-size: 26px;
  font-weight: 800;
  color: #0a0a0a;
  background: linear-gradient(135deg, #f3d96b, #c4b5fd);
  box-shadow: 0 8px 18px rgba(243, 217, 107, 0.18);
  flex-shrink: 0;
  overflow: hidden;
}

.logout-card__avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.logout-card__info {
  min-width: 0;
}

.logout-card__name {
  font-size: 18px;
  font-weight: 700;
  color: #f2f4f8;
}

.logout-card__sub {
  margin-top: 4px;
  color: #8b949e;
  font-size: 13px;
}

.logout-card__meta {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.logout-tag {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #c5cdd6;
  font-family: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
}

.logout-card__tip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(248, 113, 113, 0.06);
  border: 1px solid rgba(248, 113, 113, 0.22);
  color: #fca5a5;
  font-size: 13px;
}

.logout-card__tip .el-icon {
  font-size: 18px;
}

.logout-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 760px) {
  .settings-shell {
    grid-template-columns: 1fr;
  }

  .settings-nav {
    flex-direction: row;
    overflow-x: auto;
  }

  .account-grid {
    grid-template-columns: 1fr;
  }

  .account-fields {
    grid-template-columns: 1fr;
  }
}
</style>

<style>
/* settings 弹窗 / messagebox 暗色样式（teleport 到 body） */
.settings-dark-dialog {
  background: linear-gradient(180deg, #12161b 0%, #0f141a 100%);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 22px;
  box-shadow: 0 30px 90px rgba(0, 0, 0, 0.55);
  overflow: hidden;
  color: #e6edf3;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
}

.settings-dark-dialog .el-dialog__header {
  margin: 0;
  padding: 20px 26px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.settings-dark-dialog .el-dialog__title {
  color: #f2f4f8;
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.4px;
}

.settings-dark-dialog .el-dialog__headerbtn {
  top: 14px;
  right: 18px;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.02);
}

.settings-dark-dialog .el-dialog__headerbtn .el-dialog__close {
  color: #8b949e;
  font-size: 18px;
}

.settings-dark-dialog .el-dialog__headerbtn:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.18);
}

.settings-dark-dialog .el-dialog__headerbtn:hover .el-dialog__close {
  color: #ffffff;
}

.settings-dark-dialog .el-dialog__body {
  padding: 18px 26px 22px;
  color: #b8c2cc;
  max-height: calc(100vh - 180px);
  overflow-y: auto;
}

.settings-dark-dialog .el-form-item__label {
  color: #d5dce4;
  font-size: 13px;
  font-weight: 600;
  padding: 0 0 6px;
}

.settings-dark-dialog .el-form-item.is-error .el-form-item__error {
  color: #fca5a5;
  padding-top: 4px;
}

.settings-dark-dialog .el-input__wrapper {
  min-height: 40px;
  padding: 0 12px;
  background-color: #0c1015;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.12) inset;
  border-radius: 10px;
  color: #e6edf3;
  font-size: 13px;
}

.settings-dark-dialog .el-input__wrapper:hover {
  background-color: #0e131a;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.22) inset;
}

.settings-dark-dialog .el-input__wrapper.is-focus {
  background-color: #0d1219;
  box-shadow:
    0 0 0 1px rgba(37, 99, 235, 0.55) inset,
    0 0 0 3px rgba(37, 99, 235, 0.12);
}

.settings-dark-dialog .el-input__inner {
  color: #e6edf3;
}

.settings-dark-dialog .el-input__inner::placeholder {
  color: #7e8893;
}

.settings-dark-dialog .el-input__suffix .el-icon {
  color: #8b949e;
}

.settings-dark-dialog .el-button {
  height: 38px;
  padding: 0 18px;
  border-radius: 10px;
  font-weight: 700;
}

.settings-dark-dialog .el-button--primary {
  background-color: #2563eb;
  border-color: #2563eb;
  box-shadow: 0 8px 18px rgba(37, 99, 235, 0.22);
}

.settings-dark-dialog .el-button--primary:hover {
  background-color: #1d4ed8;
  border-color: #1d4ed8;
}

.settings-dark-dialog .el-button--danger {
  background-color: #dc2626;
  border-color: #dc2626;
  box-shadow: 0 8px 18px rgba(220, 38, 38, 0.22);
}

.settings-dark-dialog .el-button--danger:hover {
  background-color: #b91c1c;
  border-color: #b91c1c;
}

/* messagebox */
.settings-dark-messagebox {
  background: linear-gradient(180deg, #14181f 0%, #0d1117 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.55);
  color: #e6edf3;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
}

.settings-dark-messagebox .el-message-box__header {
  padding: 18px 24px 8px;
}

.settings-dark-messagebox .el-message-box__title {
  color: #e6edf3;
  font-weight: 700;
}

.settings-dark-messagebox .el-message-box__content {
  padding: 8px 24px 18px;
  color: #b8c2cc;
}

.settings-dark-messagebox .el-message-box__btns {
  padding: 12px 24px 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.settings-dark-messagebox .el-message-box__btns .el-button {
  border-radius: 8px;
}

.settings-dark-messagebox .el-message-box__btns .el-button:not(.el-button--primary):not(.el-button--danger) {
  background-color: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
  color: #c5cdd6;
}

.settings-dark-messagebox .el-message-box__btns .el-button:not(.el-button--primary):not(.el-button--danger):hover {
  background-color: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.18);
  color: #ffffff;
}
</style>