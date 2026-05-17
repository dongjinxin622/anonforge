import request from '@/request'

export interface LoginParams {
  username: string
  password: string
}

export interface LoginUserInfo {
  public_id: string
  username: string
  nickname?: string | null
}

export interface LoginResult {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: LoginUserInfo
}

export const loginApi = (data: LoginParams) => {
  return request.post<LoginResult>('/users/login', data)
}