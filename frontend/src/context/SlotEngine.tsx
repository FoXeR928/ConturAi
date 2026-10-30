import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  ReactNode,
  ComponentType,
} from "react";

export type SlotName =
  | "chat.sidebar.bottom"
  | "chat.input.actions"
  | "chat.header.right"
  | "admin.plugins.extra"
  | (string & {});

export interface SlotFill<P = any> {
  id: string;
  slotName: SlotName;
  component: ComponentType<P>;
  order?: number;
  props?: P;
}

interface SlotContextValue {
  fills: SlotFill[];
  registerComponent: <P>(fill: SlotFill<P>) => () => void;
}

const SlotContext = createContext<SlotContextValue | null>(null);

export function SlotProvider({ children }: { children: ReactNode }) {
  const [fills, setFills] = useState<SlotFill[]>([]);

  const registerComponent = useCallback(<P,>(fill: SlotFill<P>) => {
    setFills((prev) => {
      const exists = prev.findIndex((f) => f.id === fill.id);
      if (exists >= 0) {
        const next = [...prev];
        next[exists] = fill as SlotFill;
        return next;
      }
      return [...prev, fill as SlotFill];
    });
    return () => {
      setFills((prev) => prev.filter((f) => f.id !== fill.id));
    };
  }, []);

  const value = useMemo(
    () => ({ fills, registerComponent }),
    [fills, registerComponent]
  );

  return <SlotContext.Provider value={value}>{children}</SlotContext.Provider>;
}

export function useSlots(): SlotContextValue {
  const ctx = useContext(SlotContext);
  if (!ctx) throw new Error("useSlots must be used inside SlotProvider");
  return ctx;
}

export function useRegisterSlot<P = {}>(
  fill: SlotFill<P>
): ReturnType<SlotContextValue["registerComponent"]> {
  const { registerComponent } = useSlots();
  useEffect(() => {
    const unregister = registerComponent(fill);
    return unregister;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fill.id, fill.slotName]);
  return () => {};
}

interface UIExtensionSlotProps {
  name: SlotName;
  className?: string;
  fallback?: ReactNode;
}

export function UIExtensionSlot({
  name,
  className,
  fallback = null,
}: UIExtensionSlotProps) {
  const { fills } = useSlots();
  const matched = fills
    .filter((f) => f.slotName === name)
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

  if (matched.length === 0) return <>{fallback}</>;

  return (
    <div className={className} data-slot={name}>
      {matched.map((fill) => {
        const Comp = fill.component;
        return <Comp key={fill.id} {...(fill.props || {})} />;
      })}
    </div>
  );
}

// Хук для будущих плагинов: позволяет декларативно зарегистрировать fill.
export function SlotFill({
  slot,
  id,
  order,
  component,
  props,
}: {
  slot: SlotName;
  id: string;
  order?: number;
  component: ComponentType<any>;
  props?: any;
}) {
  useRegisterSlot({ id, slotName: slot, order, component, props });
  return null;
}