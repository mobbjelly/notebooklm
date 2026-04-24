import { create } from 'zustand'
import type { Notebook, Document, ChatMessage } from '../api/client'

interface AppState {
  notebooks: Notebook[]
  activeNotebook: Notebook | null
  documents: Document[]
  selectedDocIds: Set<number>
  messages: ChatMessage[]
  streamingText: string

  setNotebooks: (nbs: Notebook[]) => void
  setActiveNotebook: (nb: Notebook | null) => void
  setDocuments: (docs: Document[]) => void
  toggleDocSelected: (id: number) => void
  setAllDocsSelected: (ids: number[]) => void
  clearDocSelection: () => void
  setMessages: (msgs: ChatMessage[]) => void
  appendStreamChunk: (text: string) => void
  commitStreamMessage: (citations: string | null) => void
}

export const useAppStore = create<AppState>((set, get) => ({
  notebooks: [],
  activeNotebook: null,
  documents: [],
  selectedDocIds: new Set(),
  messages: [],
  streamingText: '',

  setNotebooks: (notebooks) => set({ notebooks }),
  setActiveNotebook: (activeNotebook) => set({ activeNotebook }),
  setDocuments: (documents) => set({ documents }),
  toggleDocSelected: (id) => set((s) => {
    const next = new Set(s.selectedDocIds)
    if (next.has(id)) next.delete(id); else next.add(id)
    return { selectedDocIds: next }
  }),
  setAllDocsSelected: (ids) => set({ selectedDocIds: new Set(ids) }),
  clearDocSelection: () => set({ selectedDocIds: new Set() }),
  setMessages: (messages) => set({ messages }),

  appendStreamChunk: (text) =>
    set((s) => ({ streamingText: s.streamingText + text })),

  commitStreamMessage: (citations) => {
    const { streamingText, messages } = get()
    if (!streamingText) return
    const msg: ChatMessage = {
      id: Date.now(),
      role: 'assistant',
      content: streamingText,
      citations,
      created_at: new Date().toISOString(),
    }
    set({ messages: [...messages, msg], streamingText: '' })
  },
}))
