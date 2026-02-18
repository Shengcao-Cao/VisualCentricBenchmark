type IdbStringStoreOptions = {
  dbName: string;
  storeName: string;
  version?: number;
};

export interface IdbStringStore {
  get(key: string): Promise<string | null>;
  getMany(keys: string[]): Promise<Record<string, string>>;
  set(key: string, value: string): Promise<boolean>;
}

export function createIdbStringStore(options: IdbStringStoreOptions): IdbStringStore {
  let dbPromise: Promise<IDBDatabase> | null = null;
  let unavailable = false;

  function openDb(): Promise<IDBDatabase> {
    if (unavailable) {
      return Promise.reject(new Error("IndexedDB unavailable"));
    }
    if (typeof window === "undefined" || !window.indexedDB) {
      unavailable = true;
      return Promise.reject(new Error("IndexedDB unavailable"));
    }
    if (dbPromise) {
      return dbPromise;
    }

    dbPromise = new Promise<IDBDatabase>((resolve, reject) => {
      const request = window.indexedDB.open(options.dbName, options.version ?? 1);

      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(options.storeName)) {
          db.createObjectStore(options.storeName);
        }
      };

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => {
        unavailable = true;
        reject(request.error ?? new Error("Failed to open IndexedDB"));
      };
      request.onblocked = () => {
        unavailable = true;
        reject(new Error("IndexedDB open blocked"));
      };
    });

    return dbPromise;
  }

  function runReadRequest(key: string): Promise<string | null> {
    return openDb()
      .then(
        (db) =>
          new Promise<string | null>((resolve, reject) => {
            const tx = db.transaction(options.storeName, "readonly");
            const store = tx.objectStore(options.storeName);
            const request = store.get(key);

            request.onsuccess = () => {
              const value = request.result;
              resolve(typeof value === "string" ? value : null);
            };
            request.onerror = () => reject(request.error ?? new Error("IndexedDB read failed"));
          })
      )
      .catch(() => null);
  }

  function runWriteRequest(key: string, value: string): Promise<boolean> {
    return openDb()
      .then(
        (db) =>
          new Promise<boolean>((resolve) => {
            const tx = db.transaction(options.storeName, "readwrite");
            const store = tx.objectStore(options.storeName);
            store.put(value, key);

            tx.oncomplete = () => resolve(true);
            tx.onerror = () => resolve(false);
            tx.onabort = () => resolve(false);
          })
      )
      .catch(() => false);
  }

  return {
    async get(key: string): Promise<string | null> {
      return runReadRequest(key);
    },
    async getMany(keys: string[]): Promise<Record<string, string>> {
      const entries = await Promise.all(
        keys.map(async (key) => {
          const value = await runReadRequest(key);
          return value === null ? null : [key, value] as const;
        })
      );
      return Object.fromEntries(entries.filter((entry): entry is readonly [string, string] => entry !== null));
    },
    async set(key: string, value: string): Promise<boolean> {
      return runWriteRequest(key, value);
    }
  };
}
