import axios from 'axios';
import type { CategoryType, CategoryValue } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Axios instance configured for the Hot Take API.
 * The Clerk JWT is attached via an interceptor set up in useAuthSync.
 */
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Attach the Clerk session token getter to the Axios instance.
 * Called once from useAuthSync after Clerk initializes.
 */
export function setAuthTokenGetter(getToken: () => Promise<string | null>) {
  api.interceptors.request.use(async (config) => {
    try {
      const token = await getToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch {
      // If token retrieval fails, proceed without auth header.
      // Protected endpoints will return 401 which callers can handle.
    }
    return config;
  });
}

/** Response shape from GET /api/categories/available */
export interface AvailableCategoriesResponse {
  [categoryType: string]: CategoryValue[];
}

/**
 * Fetch available categories with player counts.
 * Categories with fewer than 5 players are marked as disabled.
 */
export async function getAvailableCategories(): Promise<AvailableCategoriesResponse> {
  const response = await api.get<AvailableCategoriesResponse>('/api/categories/available');
  return response.data;
}

/** A single entry in a category leaderboard */
export interface CategoryLeaderboardEntry {
  rank: number;
  username: string;
  score: number;
  date: string;
}

/** Response shape from GET /api/leaderboard/category */
export interface CategoryLeaderboardResponse {
  entries: CategoryLeaderboardEntry[];
}

/**
 * Fetch the category leaderboard for a specific category value and scope.
 */
export async function getCategoryLeaderboard(
  value: string,
  scope: 'today' | 'week' | 'alltime'
): Promise<CategoryLeaderboardResponse> {
  const response = await api.get<CategoryLeaderboardResponse>('/api/leaderboard/category', {
    params: { value, scope },
  });
  return response.data;
}

/** Optional category params for quickplay/hoopiq roll generation */
export interface CategoryParams {
  category_type: CategoryType;
  category_value: string;
}

/**
 * Fetch a Quick Play roll, optionally filtered by category.
 */
export async function getQuickplayRoll<T = unknown>(categoryParams?: CategoryParams): Promise<T> {
  const response = await api.get<T>('/api/quickplay', {
    params: categoryParams,
  });
  return response.data;
}

/**
 * Fetch a HoopIQ roll, optionally filtered by category.
 */
export async function getHoopiqRoll<T = unknown>(categoryParams?: CategoryParams): Promise<T> {
  const response = await api.get<T>('/api/hoopiq', {
    params: categoryParams,
  });
  return response.data;
}

export default api;
