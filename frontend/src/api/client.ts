const API_BASE = "/api";

function getToken(): string | null {
  const saved = localStorage.getItem("user");
  if (!saved) return null;
  try {
    return JSON.parse(saved).token || null;
  } catch {
    return null;
  }
}

export class ApiError extends Error {
  constructor(
    status: number,
    message: string,
    code?: string,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.message = message;
    this.code = code;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  retries = 1,
): Promise<T> {
  const token = getToken();
  const isFormData = options.body instanceof FormData;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        headers: {
          ...(isFormData ? {} : { "Content-Type": "application/json" }),
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...options.headers,
        } as Record<string, string>,
        ...options,
      });

      // 网络层面成功，解析 body
      let body: any;
      try {
        body = await res.json();
      } catch {
        throw new ApiError(res.status, "响应格式错误");
      }

      if (!res.ok || body.code !== 0) {
        throw new ApiError(res.status, body.message || "请求失败", body.code);
      }

      return body.data as T;
    } catch (e) {
      // 网络错误（非 ApiError）且还有重试次数时重试
      if (!(e instanceof ApiError) && attempt < retries) {
        await new Promise(r => setTimeout(r, 1000));
        continue;
      }
      throw e;
    }
  }
  throw new ApiError(0, "请求失败，已重试");
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    }),
  put: <T>(path: string, data?: unknown) =>
    request<T>(path, {
      method: "PUT",
      body: data ? JSON.stringify(data) : undefined,
    }),
  delete: <T>(path: string) =>
    request<T>(path, { method: "DELETE" }),
  upload: <T>(path: string, formData: FormData) =>
    request<T>(path, { method: "POST", body: formData }),
};
