const OFFLINE_PATHS_KEY = 'offlineLearningPaths';

export const getOfflinePaths = () => {
  try {
    const data = localStorage.getItem(OFFLINE_PATHS_KEY);
    return data ? JSON.parse(data) : {};
  } catch (err) {
    console.error('Failed to read offline paths', err);
    return {};
  }
};

export const saveOfflinePath = (path) => {
  if (!path) return;
  try {
    const offline = getOfflinePaths();
    const id = path.path_id || crypto.randomUUID();
    offline[id] = { ...path, offline_id: id, saved_at: Date.now() };
    localStorage.setItem(OFFLINE_PATHS_KEY, JSON.stringify(offline));
    return id;
  } catch (err) {
    console.error('Failed to save offline path', err);
    return null;
  }
};

export const getOfflinePath = (id) => {
  if (!id) return null;
  const offline = getOfflinePaths();
  return offline[id] || null;
};

export const removeOfflinePath = (id) => {
  try {
    const offline = getOfflinePaths();
    delete offline[id];
    localStorage.setItem(OFFLINE_PATHS_KEY, JSON.stringify(offline));
  } catch (err) {
    console.error('Failed to remove offline path', err);
  }
};
