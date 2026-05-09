export type WithBusyFn = <T>(fn: () => Promise<T>) => Promise<T | undefined>
