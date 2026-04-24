import { create } from 'zustand'
import type { Notebook, Document, ChatMessage } from '../api/client'

interface AppState {
  notebooks: Notebook[]
  activeNotebook: Notebook | null
  documents: Document[]
  messages: ChatMessage[]
  streamingText: string

  setNotebooks: (nbs: Notebook[]) => void
  setActiveNotebook: (nb: Notebook | null) => void
  setDocuments: (docs: Document[]) => void
  setMessages: (msgs: ChatMessage[]) => void
  appendStreamChunk: (text: string) => void
  commitStreamMessage: (citations: string | null) => void
}

export const useAppStore = create<AppState>((set, get) => ({
  notebooks: [],
  activeNotebook: null,
  documents: [],
  messages: [],
  streamingText: '',

  setNotebooks: (notebooks) => set({ notebooks }),
  setActiveNotebook: (activeNotebook) => set({ activeNotebook }),
  setDocuments: (documents) => set({ documents }),
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
