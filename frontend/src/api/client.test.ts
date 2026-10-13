import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { api } from './client'

describe('API Client', () => {
  const originalFetch = global.fetch

  beforeEach(() => {
    global.fetch = vi.fn()
  })

  afterEach(() => {
    global.fetch = originalFetch
    vi.resetAllMocks()
  })

  it('should successfully parse a JSON response', async () => {
    const mockCases = [{ id: '1', name: 'Test Case' }]
    vi.mocked(global.fetch).mockResolvedValueOnce(new Response(JSON.stringify(mockCases), { status: 200 }))

    const result = await api.listCases()

    expect(global.fetch).toHaveBeenCalledWith('/api/cases', undefined)
    expect(result).toEqual(mockCases)
  })

  it('should handle 204 No Content', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce(new Response(null, { status: 204 }))

    const result = await api.deleteEvidence('case1', 'ev1')

    expect(global.fetch).toHaveBeenCalledWith('/api/cases/case1/evidence/ev1', { method: 'DELETE' })
    expect(result).toBeUndefined()
  })

  it('should pass options properly, such as POST with JSON body', async () => {
    const mockCase = { id: '2', name: 'New Case' }
    vi.mocked(global.fetch).mockResolvedValueOnce(new Response(JSON.stringify(mockCase), { status: 200 }))

    const data = { name: 'New Case' }
    const result = await api.createCase(data)

    expect(global.fetch).toHaveBeenCalledWith('/api/cases', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    expect(result).toEqual(mockCase)
  })

  it('should handle FormData in uploadEvidence', async () => {
    const mockEvidence = { id: 'ev2', name: 'File' }
    vi.mocked(global.fetch).mockResolvedValueOnce(new Response(JSON.stringify(mockEvidence), { status: 200 }))

    const file = new File(['content'], 'test.txt', { type: 'text/plain' })
    const result = await api.uploadEvidence('case1', file, 'bank_statement')

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/cases/case1/evidence',
      expect.objectContaining({ method: 'POST' })
    )
    expect(result).toEqual(mockEvidence)

    const fetchArgs = vi.mocked(global.fetch).mock.calls[0]
    const options = fetchArgs[1]
    expect(options?.body).toBeInstanceOf(FormData)
    const formData = options?.body as FormData
    expect(formData.get('file')).toBe(file)
    expect(formData.get('category')).toBe('bank_statement')
  })

  it('should throw an error with details when response is not ok and JSON has detail', async () => {
    const errorBody = { detail: 'Something went wrong' }
    vi.mocked(global.fetch).mockResolvedValueOnce(new Response(JSON.stringify(errorBody), { status: 400 }))

    await expect(api.getCase('1')).rejects.toThrow('Something went wrong')
  })

  it('should throw an error with fallback when response is not ok and no detail is present', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce(new Response('Internal Server Error', { status: 500 }))

    await expect(api.getCase('1')).rejects.toThrow('Request failed: 500')
  })
})
