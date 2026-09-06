import { useState, useEffect } from 'react';

const STORAGE_KEY = 'jhtracker_visited_jobs_v1';

export interface VisitedRecord {
  jobId: string;
  visitedAt: number;
}

export const visitedStorage = {
  getVisitedIds(): Set<string> {
    try {
      const data = localStorage.getItem(STORAGE_KEY);
      if (!data) return new Set();
      const parsed: string[] = JSON.parse(data);
      return new Set(parsed);
    } catch {
      return new Set();
    }
  },

  markVisited(jobId: string): void {
    if (!jobId) return;
    try {
      const set = this.getVisitedIds();
      set.add(jobId);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(set)));
      window.dispatchEvent(new CustomEvent('visited_jobs_updated'));
    } catch (e) {
      console.error('Failed to save visited job to localStorage', e);
    }
  },

  isVisited(jobId: string): boolean {
    return this.getVisitedIds().has(jobId);
  },

  clearAll(): void {
    localStorage.removeItem(STORAGE_KEY);
    window.dispatchEvent(new CustomEvent('visited_jobs_updated'));
  }
};

export function useVisitedJobs() {
  const [visitedSet, setVisitedSet] = useState<Set<string>>(() => visitedStorage.getVisitedIds());

  useEffect(() => {
    const handleUpdate = () => {
      setVisitedSet(visitedStorage.getVisitedIds());
    };
    window.addEventListener('visited_jobs_updated', handleUpdate);
    return () => window.removeEventListener('visited_jobs_updated', handleUpdate);
  }, []);

  return {
    visitedSet,
    markVisited: (id: string) => visitedStorage.markVisited(id),
    clearVisited: () => visitedStorage.clearAll()
  };
}
