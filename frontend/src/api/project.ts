import request from '@/request'

export type ProjectVideoMode =
  | 'text'
  | 'singleImage'
  | 'startEndRequired'
  | 'endFrameOptional'
  | 'startFrameOptional'

export type ProjectMemberRole = 'owner' | 'admin' | 'manager' | 'editor' | 'viewer'

export interface ProjectRecord {
  id: number
  public_id: string
  owner_id: string
  name: string
  intro: string
  project_type: string
  content_type: string
  art_style: string
  director_manual: string
  video_ratio: string
  image_model: string
  video_model: string
  image_quality: string
  mode: ProjectVideoMode
  my_role?: ProjectMemberRole | null
  sort_order: number
  created_at: string
  updated_at: string
  disabled_at?: string | null
}

export interface ProjectPayload {
  name: string
  intro: string
  project_type: string
  content_type: string
  art_style: string
  director_manual: string
  video_ratio: string
  image_model: string
  video_model: string
  image_quality: string
  mode: ProjectVideoMode
}

export interface ProjectMemberRecord {
  id: number
  project_id: number
  user_public_id: string
  role: ProjectMemberRole
  joined_at: string
}

export interface ProjectMemberInvitePayload {
  user_public_id: string
  role: ProjectMemberRole
}

export interface UserRecord {
  public_id: string
  username: string
  nickname?: string | null
  email?: string | null
  avatar_url?: string | null
  sort_order: number
  is_superuser: boolean
  disabled_at?: string | null
  last_login_at?: string | null
  created_at: string
  updated_at: string
}

export const listProjectsApi = () => request.get<ProjectRecord[]>('/projects/')

export const searchProjectsByNameApi = (name: string) => (
  request.get<ProjectRecord[]>('/projects/search/by-name', { params: { name } })
)

export const createProjectApi = (data: ProjectPayload) => request.post<ProjectRecord>('/projects/', data)

export const updateProjectApi = (publicId: string, data: Partial<ProjectPayload>) => (
  request.put<ProjectRecord>(`/projects/${publicId}`, data)
)

export const disableProjectApi = (publicId: string) => request.patch<ProjectRecord>(`/projects/${publicId}/disable`)

export const enableProjectApi = (publicId: string) => request.patch<ProjectRecord>(`/projects/${publicId}/enable`)

export const deleteProjectApi = (publicId: string) => request.delete(`/projects/${publicId}`)

export const listProjectMembersApi = (publicId: string) => (
  request.get<ProjectMemberRecord[]>(`/projects/${publicId}/members`)
)

export const searchProjectMemberCandidatesApi = (publicId: string, keyword: string) => (
  request.get<UserRecord[]>(`/projects/${publicId}/members/candidates`, { params: { keyword } })
)

export const inviteProjectMemberApi = (publicId: string, data: ProjectMemberInvitePayload) => (
  request.post<ProjectMemberRecord>(`/projects/${publicId}/members/invitations`, data)
)

export const updateProjectMemberRoleApi = (
  publicId: string,
  userPublicId: string,
  role: ProjectMemberRole,
) => (
  request.patch<ProjectMemberRecord>(`/projects/${publicId}/members/${userPublicId}`, null, { params: { role } })
)

export const removeProjectMemberApi = (publicId: string, userPublicId: string) => (
  request.delete(`/projects/${publicId}/members/${userPublicId}`)
)