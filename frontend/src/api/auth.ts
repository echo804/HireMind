import { api } from "./client";

export interface AuthResponse {
  id: string;
  email: string;
  nickname: string;
  token: string;
}

export interface LoginParams {
  email: string;
  password: string;
}

export interface RegisterParams {
  email: string;
  password: string;
  nickname: string;
}

export const authApi = {
  login: (params: LoginParams) =>
    api.post<AuthResponse>("/auth/login", params),

  register: (params: RegisterParams) =>
    api.post<AuthResponse>("/auth/register", params),
};
