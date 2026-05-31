import request from '@/request'

export type EventState = -1 | 0 | 1

export interface NovelChapterRecord {
  id: number
  publicId: string
  projectId: number
  chapterIndex: number
  reel: string
  chapter: string
  chapterData: string
  event: string
  eventState: EventState
  errorReason: string | null
  crawlSourceKey: string
  crawlNovelDirid: string
  crawlChapterId: number | null
  crawlTime: string
  crawlMd5: string
  sortOrder: number
  createdAt: string
  updatedAt: string
  disabledAt: string | null
}

export interface NovelChapterPage {
  data: NovelChapterRecord[]
  total: number
  page: number
  limit: number
}

export interface NovelChapterListParams {
  page: number
  limit: number
  search?: string
}

export interface NovelChapterPayload {
  chapterIndex: number
  reel: string
  chapter: string
  chapterData: string
  event?: string
}

export interface NovelChapterBatchPayload {
  ids: number[]
}

export interface NovelChapterBatchResult {
  affected: number
}

export interface NovelChapterImportItemPayload {
  reel: string
  chapter: string
  chapterData: string
}

export interface NovelChapterImportPayload {
  rawText?: string
  chapters?: NovelChapterImportItemPayload[]
}

export interface NovelImportSplitRule {
  key: string
  label: string
  description: string
  chapterPattern: string
  chapterFlagsList: string[]
  reelPattern: string
  reelFlagsList: string[]
  builtin: boolean
}

export type CrawlSourceType = 'rule' | 'api'
export type CrawlSourceScope = 'public' | 'private'
export type CrawlHttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export const CRAWL_HTTP_METHODS: CrawlHttpMethod[] = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
export const CRAWL_HTTP_METHODS_WITH_BODY: ReadonlyArray<CrawlHttpMethod> = ['POST', 'PUT', 'PATCH']

export interface CrawlSourcePayload {
  key: string
  name: string
  baseUrl: string
  desc: string
  sourceType: CrawlSourceType
  searchUrlTemplate: string
  listItemSelector: string
  listTitleSelector: string
  listAuthorSelector: string
  listLinkSelector: string
  detailTitleSelector: string
  detailContentSelector: string
  detailNextSelector: string
  apiBookUrl: string
  apiBookTitlePath: string
  apiBookAuthorPath: string
  apiBookIntroPath: string
  apiBookLastChapterIdPath: string
  apiBookCoverPath: string
  apiChapterUrl: string
  apiChapterNamePath: string
  apiChapterContentPath: string
  apiChapterTimePath: string
  apiChapterMd5Path: string
  apiSearchMethod: CrawlHttpMethod
  apiSearchHeaders: string
  apiSearchBody: string
  apiBookMethod: CrawlHttpMethod
  apiBookHeaders: string
  apiBookBody: string
  apiChapterMethod: CrawlHttpMethod
  apiChapterHeaders: string
  apiChapterBody: string
  builtin: boolean
  projectPublicId?: string | null
}

export type CrawlSourceUpdatePayload = Partial<Omit<CrawlSourcePayload, 'key' | 'projectPublicId' | 'builtin'>>

export interface CrawlSourceRecord extends CrawlSourcePayload {
  id: number
  publicId: string
  projectPublicId: string | null
  scope: CrawlSourceScope
  sortOrder: number
  createdAt: string
  updatedAt: string
  disabledAt: string | null
}

export interface CrawlSearchResult {
  dirid: string
  id: number
  full: string
  title: string
  author: string
  cover: string
  lastchapter: string
  lastchapterid: number
  lastupdate: string
  sortname: string
  intro: string
  sourceKey: string
}

export interface CrawlChapterDraft {
  key: number
  novelDirid: string
  chapterid: number
  chaptername: string
  time: string
  txt: string
  md5: string
  event: string
  eventState: EventState
  errorReason: string | null
}

export type CrawlChapterStreamEvent =
  | {
      type: 'start'
      total: number
      startChapter: number
      endChapter: number
    }
  | {
      type: 'chapter'
      completed: number
      total: number
      chapter: CrawlChapterDraft
    }
  | {
      type: 'done'
      completed: number
      total: number
    }
  | {
      type: 'error'
      detail: string
      completed: number
      total: number
    }

export interface CrawlSearchPayload {
  sourceKey: string
  query: string
}

export interface CrawlChapterFetchPayload {
  sourceKey: string
  book: CrawlSearchResult
  startChapter: number
  endChapter: number
}

export interface CrawlImportPayload {
  sourceKey: string
  book: CrawlSearchResult
  chapters: CrawlChapterDraft[]
}

export interface CrawlImportResult {
  created: number
  updated: number
  skipped: number
  chapters: NovelChapterRecord[]
}

export interface CrawlAnalyzePayload {
  url: string
  sourceType: CrawlSourceType
}

export interface CrawlAnalyzeResult {
  status: 'pending'
  source: CrawlSourcePayload
  message: string
}

export const listNovelChaptersApi = (
  projectPublicId: string,
  params: NovelChapterListParams,
) => (
  request.get<NovelChapterPage>(`${projectNovelPath(projectPublicId)}`, { params })
)

export const createNovelChapterApi = (
  projectPublicId: string,
  payload: NovelChapterPayload,
) => (
  request.post<NovelChapterRecord>(`${projectNovelPath(projectPublicId)}`, payload)
)

export const importNovelChaptersApi = (
  projectPublicId: string,
  payload: NovelChapterImportPayload,
) => (
  request.post<NovelChapterRecord[]>(`${projectNovelPath(projectPublicId)}/import`, payload, { timeout: 120000 })
)

export const listNovelImportSplitRulesApi = (
  projectPublicId: string,
) => (
  request.get<NovelImportSplitRule[]>(`${projectNovelPath(projectPublicId)}/import-split-rules`)
)

export const updateNovelChapterApi = (
  projectPublicId: string,
  chapterId: number,
  payload: Partial<NovelChapterPayload>,
) => (
  request.put<NovelChapterRecord>(`${projectNovelPath(projectPublicId)}/${chapterId}`, payload)
)

export const deleteNovelChapterApi = (
  projectPublicId: string,
  chapterId: number,
) => (
  request.delete<void>(`${projectNovelPath(projectPublicId)}/${chapterId}`)
)

export const batchDeleteNovelChaptersApi = (
  projectPublicId: string,
  payload: NovelChapterBatchPayload,
) => (
  request.post<NovelChapterBatchResult>(`${projectNovelPath(projectPublicId)}/batch-delete`, payload)
)

export const cleanNovelChapterApi = (
  projectPublicId: string,
  chapterId: number,
) => (
  request.post<NovelChapterRecord>(`${projectNovelPath(projectPublicId)}/${chapterId}/clean`, undefined, { timeout: 120000 })
)

export const batchCleanNovelChaptersApi = (
  projectPublicId: string,
  payload: NovelChapterBatchPayload,
) => (
  request.post<NovelChapterBatchResult>(`${projectNovelPath(projectPublicId)}/batch-clean`, payload, { timeout: 120000 })
)

export const listCrawlSourcesApi = (
  projectPublicId: string,
) => (
  request.get<CrawlSourceRecord[]>(`${projectNovelPath(projectPublicId)}/crawl-sources`)
)

export const createCrawlSourceApi = (
  projectPublicId: string,
  payload: CrawlSourcePayload,
) => (
  request.post<CrawlSourceRecord>(`${projectNovelPath(projectPublicId)}/crawl-sources`, payload)
)

export const updateCrawlSourceApi = (
  projectPublicId: string,
  key: string,
  payload: CrawlSourceUpdatePayload,
) => (
  request.put<CrawlSourceRecord>(
    `${projectNovelPath(projectPublicId)}/crawl-sources/${encodeURIComponent(key.trim())}`,
    payload,
  )
)

export const deleteCrawlSourceApi = (
  projectPublicId: string,
  key: string,
) => (
  request.delete<void>(`${projectNovelPath(projectPublicId)}/crawl-sources/${encodeURIComponent(key.trim())}`)
)

export interface CrawlSourceDuplicatePayload {
  newKey: string
  name?: string
}

export const duplicateCrawlSourceApi = (
  projectPublicId: string,
  key: string,
  payload: CrawlSourceDuplicatePayload,
) => (
  request.post<CrawlSourceRecord>(
    `${projectNovelPath(projectPublicId)}/crawl-sources/${encodeURIComponent(key.trim())}/duplicate`,
    payload,
  )
)

export const analyzeCrawlSourceApi = (
  projectPublicId: string,
  payload: CrawlAnalyzePayload,
) => (
  request.post<CrawlAnalyzeResult>(`${projectNovelPath(projectPublicId)}/crawl-sources/analyze`, payload)
)

export const searchCrawlBooksApi = (
  projectPublicId: string,
  payload: CrawlSearchPayload,
) => (
  request.post<CrawlSearchResult[]>(`${projectNovelPath(projectPublicId)}/crawl/search`, payload, { timeout: 120000 })
)

export const fetchCrawlChaptersApi = (
  projectPublicId: string,
  payload: CrawlChapterFetchPayload,
) => (
  request.post<CrawlChapterDraft[]>(`${projectNovelPath(projectPublicId)}/crawl/chapters`, payload, { timeout: 120000 })
)

export const crawlChaptersStreamUrl = (projectPublicId: string) => (
  `/api${projectNovelPath(projectPublicId)}/crawl/chapters/stream`
)

export const importCrawlChaptersApi = (
  projectPublicId: string,
  payload: CrawlImportPayload,
) => (
  request.post<CrawlImportResult>(`${projectNovelPath(projectPublicId)}/crawl/import`, payload, { timeout: 120000 })
)

const projectNovelPath = (projectPublicId: string) => (
  `/projects/${encodeURIComponent(projectPublicId.trim())}/novels`
)
