const DB_NAME = 'learni_offline';
const DB_VERSION = 1;
const STORE_NAME = 'paths';
const LEGACY_KEY = 'offlineLearningPaths';

let dbPromise = null;
let migrationAttempted = false;

export const generateUUID = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
};

// Initialize/open IndexedDB
const initDB = () => {
  if (dbPromise) return dbPromise;
  dbPromise = new Promise((resolve, reject) => {
    try {
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = (event) => {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, { keyPath: 'offline_id' });
          store.createIndex('saved_at', 'saved_at', { unique: false });
        }
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    } catch (err) {
      reject(err);
    }
  });
  return dbPromise;
};

// Helper to run a transaction
const withStore = async (mode, callback) => {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, mode);
    const store = tx.objectStore(STORE_NAME);
    const result = callback(store);
    tx.oncomplete = () => resolve(result);
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error || new Error('Transaction aborted'));
  });
};

// Estimate storage usage/quota if available
export const estimateUsage = async () => {
  if (typeof navigator !== 'undefined' && navigator.storage && navigator.storage.estimate) {
    try {
      const { usage, quota } = await navigator.storage.estimate();
      return { usedBytes: usage || 0, quotaBytes: quota || undefined };
    } catch (err) {
      // Fallback: compute by summing record sizes
    }
  }
  // Fallback: sum JSON sizes
  const all = await getOfflinePathsIndex(true);
  const usedBytes = all.reduce((sum, meta) => sum + (meta.size_bytes || 0), 0);
  return { usedBytes };
};

// One-time migration from legacy localStorage blob to IndexedDB
const migrateFromLocalStorage = async () => {
  if (migrationAttempted) return;
  migrationAttempted = true;
  try {
    const data = localStorage.getItem(LEGACY_KEY);
    if (!data) return;
    let parsed = {};
    try {
      parsed = JSON.parse(data) || {};
    } catch (e) {
      console.warn('Legacy offline data is corrupted; skipping migration');
      return;
    }
    const entries = Object.values(parsed);
    if (entries.length === 0) {
      localStorage.removeItem(LEGACY_KEY);
      return;
    }
    // Write each entry into IDB
    await withStore('readwrite', (store) => {
      for (const item of entries) {
        const offline_id = item.offline_id || item.path_id || generateUUID();
        const serialized = JSON.stringify(item);
        const size_bytes = new Blob([serialized]).size;
        const record = {
          offline_id,
          saved_at: item.saved_at || Date.now(),
          size_bytes,
          path_data: item,
        };
        store.put(record);
      }
    });
    // Clear legacy store after successful migration
    localStorage.removeItem(LEGACY_KEY);
    console.info(`Migrated ${entries.length} offline course(s) from localStorage to IndexedDB.`);
  } catch (err) {
    console.warn('Failed to migrate legacy offline data:', err);
  }
};

// List index of offline paths (metadata only)
// If includeSize is true, ensure size_bytes is present (compute if missing)
export const getOfflinePathsIndex = async (includeSize = false) => {
  await migrateFromLocalStorage();
  const items = [];
  await withStore('readonly', (store) => {
    const request = store.openCursor();
    request.onsuccess = (e) => {
      const cursor = e.target.result;
      if (cursor) {
        const value = cursor.value;
        const topic = value?.path_data?.topic || 'Untitled Course';
        const meta = {
          offline_id: value.offline_id,
          topic,
          saved_at: value.saved_at,
          size_bytes: value.size_bytes,
        };
        items.push(meta);
        cursor.continue();
      }
    };
  });
  if (includeSize) {
    // Compute missing sizes lazily
    const updated = [];
    for (const meta of items) {
      if (!meta.size_bytes) {
        const full = await getOfflinePathRecord(meta.offline_id);
        if (full) {
          const serialized = JSON.stringify(full.path_data);
          meta.size_bytes = new Blob([serialized]).size;
          // Persist updated size_bytes
          await withStore('readwrite', (store) => store.put({ ...full, size_bytes: meta.size_bytes }));
        }
      }
      updated.push(meta);
    }
    return updated;
  }
  return items;
};

// Internal: get full record from IDB
const getOfflinePathRecord = async (offlineId) => {
  await migrateFromLocalStorage();
  let record = null;
  await withStore('readonly', (store) => {
    const req = store.get(offlineId);
    req.onsuccess = (e) => {
      record = e.target.result || null;
    };
  });
  return record;
};

// Public: get offline path (returns the stored learning path data)
export const getOfflinePath = async (offlineId) => {
  const record = await getOfflinePathRecord(offlineId);
  if (!record) return null;
  // Return the original structure with offline_id present
  return { ...record.path_data, offline_id: record.offline_id };
};

// Evict oldest entries until enough space is presumed available, then attempt a callback
const evictIfNeededAndRetry = async (attemptWrite) => {
  // First try without eviction
  try {
    return await attemptWrite();
  } catch (err) {
    // If not quota-related, rethrow
    const msg = String(err?.message || err);
    if (!/quota|QuotaExceededError|capacity/i.test(msg)) throw err;
  }

  // Evict in small batches and retry
  const index = await getOfflinePathsIndex();
  // Sort by saved_at ascending (oldest first)
  index.sort((a, b) => (a.saved_at || 0) - (b.saved_at || 0));

  for (let i = 0; i < index.length; i++) {
    try {
      await removeOfflinePath(index[i].offline_id);
      // Try write again
      try {
        return await attemptWrite();
      } catch (err) {
        const msg = String(err?.message || err);
        if (!/quota|QuotaExceededError|capacity/i.test(msg)) throw err;
        // Otherwise continue evicting
      }
    } catch (evictErr) {
      // Continue eviction attempts even if a deletion fails
      console.warn('Failed to evict offline entry during quota recovery:', evictErr);
    }
  }
  throw new Error('Storage quota exceeded: Unable to save offline course even after eviction.');
};

// Save a learning path for offline use; returns offline_id
export const saveOfflinePath = async (path) => {
  if (!path) return null;
  await migrateFromLocalStorage();
  const offline_id = path.path_id || path.offline_id || generateUUID();
  const now = Date.now();
  const record = {
    offline_id,
    saved_at: now,
    path_data: { ...path, offline_id, saved_at: now },
  };
  const serialized = JSON.stringify(record.path_data);
  record.size_bytes = new Blob([serialized]).size;

  const attemptWrite = async () => {
    await withStore('readwrite', (store) => store.put(record));
    return offline_id;
  };

  try {
    return await evictIfNeededAndRetry(attemptWrite);
  } catch (err) {
    console.error('Failed to save offline path', err);
    return null;
  }
};

// Remove an offline path by id
export const removeOfflinePath = async (offlineId) => {
  await migrateFromLocalStorage();
  try {
    await withStore('readwrite', (store) => store.delete(offlineId));
  } catch (err) {
    console.error('Failed to remove offline path', err);
  }
};

// Backward-compat getOfflinePaths: return map of id->path for UI compatibility if needed
// Prefer using getOfflinePathsIndex for listing
export const getOfflinePaths = async () => {
  const index = await getOfflinePathsIndex();
  const result = {};
  for (const meta of index) {
    const item = await getOfflinePath(meta.offline_id);
    if (item) result[meta.offline_id] = item;
  }
  return result;
};
