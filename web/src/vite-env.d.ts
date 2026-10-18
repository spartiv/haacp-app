/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** API origin for production builds. Empty in dev: requests go through the Vite proxy. */
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
