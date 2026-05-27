import { create } from 'zustand';

interface UIState {
  isSidebarOpen: boolean;
  isDarkMode: boolean;
  activeModal: string | null;
  toggleSidebar: () => void;
  toggleDarkMode: () => void;
  openModal: (modalId: string) => void;
  closeModal: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  isSidebarOpen: true,
  isDarkMode: false,
  activeModal: null,
  
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  
  toggleDarkMode: () => set((state) => {
    const newMode = !state.isDarkMode;
    document.documentElement.classList.toggle('dark', newMode);
    return { isDarkMode: newMode };
  }),
  
  openModal: (modalId: string) => set({ activeModal: modalId }),
  
  closeModal: () => set({ activeModal: null }),
}));
