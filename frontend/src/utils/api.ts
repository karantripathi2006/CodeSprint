const API_BASE = 'http://localhost:8000/api/v1';

export function getToken() {
  return localStorage.getItem('access_token');
}

export function setToken(token: string) {
  localStorage.setItem('access_token', token);
}

export function removeToken() {
  localStorage.removeItem('access_token');
}

export async function authFetch(path: string, options: RequestInit = {}) {
  const token = getToken();
  
  if (!options.headers) {
    options.headers = new Headers();
  } else if (!(options.headers instanceof Headers)) {
    options.headers = new Headers(options.headers);
  }

  if (token) {
    (options.headers as Headers).append('Authorization', `Bearer ${token}`);
  }
  
  // If not FormData, assuming JSON by default if we have a body
  if (options.body && !(options.body instanceof FormData) && !(options.headers as Headers).has('Content-Type')) {
    (options.headers as Headers).append('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE}${path}`, options);
  
  if (response.status === 401) {
    removeToken();
    window.dispatchEvent(new Event('unauthorized'));
    throw new Error('Session expired. Please login again.');
  }
  
  return response;
}
