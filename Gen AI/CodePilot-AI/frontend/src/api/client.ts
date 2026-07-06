import axios from "axios";

// Environment variable VITE_API_URL can be set in .env
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export interface APIResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
  details?: any[];
}
