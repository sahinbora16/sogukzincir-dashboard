import { create } from 'zustand';
import type { Vehicle, StorageTank, Alert } from '../types';

interface DashboardState {
  vehicles: Vehicle[];
  tanks: StorageTank[];
  alerts: Alert[];
  wsConnected: boolean;
  setVehicles: (vehicles: Vehicle[]) => void;
  updateVehicle: (update: Partial<Vehicle> & { id: number }) => void;
  setTanks: (tanks: StorageTank[]) => void;
  updateTank: (update: Partial<StorageTank> & { id: number }) => void;
  setAlerts: (alerts: Alert[]) => void;
  resolveAlert: (id: number) => void;
  setWsConnected: (connected: boolean) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  vehicles: [],
  tanks: [],
  alerts: [],
  wsConnected: false,

  setVehicles: (vehicles) => set({ vehicles }),
  updateVehicle: (update) =>
    set((state) => ({
      vehicles: state.vehicles.map((v) =>
        v.id === update.id ? { ...v, ...update } : v,
      ),
    })),

  setTanks: (tanks) => set({ tanks }),
  updateTank: (update) =>
    set((state) => ({
      tanks: state.tanks.map((t) =>
        t.id === update.id ? { ...t, ...update } : t,
      ),
    })),

  setAlerts: (alerts) => set({ alerts }),
  resolveAlert: (id) =>
    set((state) => ({
      alerts: state.alerts.map((a) =>
        a.id === id ? { ...a, resolved: true } : a,
      ),
    })),

  setWsConnected: (wsConnected) => set({ wsConnected }),
}));
