import { getClientId } from '../store/clientId'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api'

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      'X-Client-ID': getClientId(),
      ...init.headers,
    },
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }))
    throw new Error(err.detail ?? 'Request failed')
  }
  return resp.json()
}

export const api = {
  // Notebooks
  getNotebooks: () => request<Notebook[]>('/notebooks'),
  createNotebook: (data: { name: string; description?: string }) =>
    request<Notebook>('/notebooks', { method: 'POST', body: JSON.stringify(data) }),
  updateNotebook: (id: number, data: Partial<{ name: string; description: string }>) =>
    request<Notebook>(`/notebooks/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteNotebook: (id: number) =>
    request<void>(`/notebooks/${id}`, { method: 'DELETE' }),
  shareNotebook: (id: number) =>
    request<Notebook>(`/notebooks/${id}/share`, { method: 'POST' }),

  // Documents
  getDocuments: (notebookId: number) =>
    request<Document[]>(`/notebooks/${notebookId}/documents`),
  uploadFile: (notebookId: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<Document>(`/notebooks/${notebookId}/documents/upload`, {
      method: 'POST',
      body: form,
      headers: { 'X-Client-ID': getClientId() },  // 不带 Content-Type，让浏览器设 multipart
    })
  },
  addUrl: (notebookId: number, url: string, name?: string) =>
    request<Document>(`/notebooks/${notebookId}/documents/url`, {
      method: 'POST',
      body: JSON.stringify({ url, name }),
    }),
  deleteDocument: (notebookId: number, docId: number) =>
    request<void>(`/notebooks/${notebookId}/documents/${docId}`, { method: 'DELETE' }),
  updateNotes: (notebookId: number, docId: number, user_notes: string) =>
    request<Document>(`/notebooks/${notebookId}/documents/${docId}/notes`, {
      method: 'PATCH',
      body: JSON.stringify({ user_notes }),
    }),

  // Chat history
  getChatHistory: (notebookId: number) =>
    request<ChatMessage[]>(`/notebooks/${notebookId}/chat`),

  // Analysis
  getAnalysis: (notebookId: number) =>
    request<{ result: AnalysisResult | null }>(`/notebooks/${notebookId}/analysis`),
  triggerAnalysis: (notebookId: number) =>
    request<{ result: AnalysisResult }>(`/notebooks/${notebookId}/analysis`, { method: 'POST' }),
}

// SSE 流式聊天
export function chatStream(
  notebookId: number,
  question: string,
  docId: number | null,
  onChunk: (text: string) => void,
  onDone: (citations: Citation[]) => void,
  onError: (err: Error) => void,
) {
  fetch(`${BASE_URL}/notebooks/${notebookId}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Client-ID': getClientId(),
    },
    body: JSON.stringify({ question, doc_id: docId }),
  }).then(async (resp) => {
    if (!resp.ok) throw new Error('Chat request failed')
    const reader = resp.body!.getReader()
    const decoder = new TextDecoder()
    let buf = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const lines = buf.split('\n')
      buf = lines.pop() ?? ''
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const payload = JSON.parse(line.slice(6))
        if (payload.text) onChunk(payload.text)
        if (payload.done) onDone(payload.citations ?? [])
      }
    }
  }).catch(onError)
}

// Types
export interface Notebook {
  id: number
  name: string
  description: string | null
  share_token: string | null
  doc_count: number
  created_at: string
  updated_at: string
}

export interface Document {
  id: number
  notebook_id: number
  name: string
  doc_type: string
  status: 'pending' | 'processing' | 'ready' | 'failed'
  chunk_count: number
  summary_text: string | null
  key_points: string | null
  ai_notes: string | null
  user_notes: string | null
  error_msg: string | null
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  citations: string | null
  created_at: string
}

export interface Citation {
  doc_id: number
  doc_name: string
  chunk_index: number
  text: string
  score: number
}

export interface AnalysisResult {
  common_themes: string[]
  differences: string[]
  blind_spots: string[]
  synthesis: string
}
