<template>
  <div class="wechat-studio">
    <!-- Header -->
    <header class="studio-header">
      <div class="header-content">
        <h1 class="page-title">
          <span class="title-accent">WeChat</span> Studio
        </h1>
        <p class="page-subtitle">Chat with AI, export notes, and publish to WeChat</p>
      </div>
    </header>

    <!-- Main Content -->
    <div class="studio-content">
      <!-- Left: Chat Area -->
      <div class="chat-panel">
        <div class="panel-header">
          <h3>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/>
            </svg>
            AI Assistant
          </h3>
          <div class="panel-actions">
            <button class="action-btn" @click="clearChat" title="Clear chat">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Chat Messages -->
        <div class="chat-messages" ref="chatContainer">
          <div v-if="messages.length === 0" class="empty-chat">
            <div class="empty-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/>
              </svg>
            </div>
            <p>Start a conversation with AI</p>
            <span class="hint">Ask for article ideas, writing help, or content suggestions</span>
          </div>

          <div v-else class="messages-list">
            <div
              v-for="(msg, index) in messages"
              :key="index"
              class="message"
              :class="{ 'user': msg.role === 'user', 'assistant': msg.role === 'assistant' }"
            >
              <div class="message-avatar">
                <span v-if="msg.role === 'user'">You</span>
                <span v-else>AI</span>
              </div>
              <div class="message-content">
                <div class="message-text" v-html="renderMarkdown(msg.content)"></div>
                <div v-if="msg.role === 'assistant'" class="message-actions">
                  <button class="msg-action" @click="copyMessage(msg.content)" title="Copy">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                      <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <!-- Streaming Message -->
            <div v-if="isStreaming" class="message assistant streaming">
              <div class="message-avatar">AI</div>
              <div class="message-content">
                <div class="message-text" v-html="renderMarkdown(streamingContent)"></div>
                <div class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Chat Input -->
        <div class="chat-input-area">
          <div class="input-wrapper">
            <textarea
              v-model="userInput"
              class="chat-input"
              placeholder="Type your message... (Shift+Enter to send)"
              rows="3"
              @keydown="handleKeydown"
              :disabled="isStreaming"
            ></textarea>
            <div class="input-actions">
              <button
                class="send-btn"
                :class="{ 'active': userInput.trim() && !isStreaming }"
                @click="sendMessage"
                :disabled="!userInput.trim() || isStreaming"
              >
                <svg v-if="!isStreaming" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="22" y1="2" x2="11" y2="13"/>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spinning">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 2a10 10 0 0 1 10 10"/>
                </svg>
              </button>
            </div>
          </div>
          <div class="quick-actions">
            <button class="quick-btn" @click="sendQuickMessage('帮我写一篇关于AI的技术文章')">
              📝 Write tech article
            </button>
            <button class="quick-btn" @click="sendQuickMessage('给我一些微信公众号选题建议')">
              💡 Topic ideas
            </button>
            <button class="quick-btn" @click="sendQuickMessage('优化这段内容的标题')">
              ✨ Optimize title
            </button>
          </div>
        </div>
      </div>

      <!-- Right: Note Editor -->
      <div class="editor-panel">
        <!-- Export Dialog -->
        <Teleport to="body">
          <Transition name="dialog">
            <div v-if="showExportDialog" class="export-dialog-overlay" @click.self="closeExportDialog">
              <div class="export-dialog">
                <div class="dialog-header">
                  <h3>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M12 5v14M5 12l7 7 7-7"/>
                    </svg>
                    Export to Note Editor
                  </h3>
                  <button class="close-btn" @click="closeExportDialog">&times;</button>
                </div>

                <div class="dialog-content">
                  <!-- Template Selection -->
                  <div class="template-section">
                    <label class="section-label">Choose Template</label>
                    <div class="template-grid">
                      <div
                        v-for="template in exportTemplates"
                        :key="template.id"
                        class="template-card"
                        :class="{ active: selectedTemplate === template.id }"
                        @click="selectedTemplate = template.id"
                      >
                        <span class="template-icon">{{ template.icon }}</span>
                        <span class="template-name">{{ template.name }}</span>
                        <span class="template-desc">{{ template.description }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- Message Selection -->
                  <div class="messages-section">
                    <div class="section-header">
                      <label class="section-label">Select Messages</label>
                      <div class="selection-actions">
                        <button class="text-btn" @click="selectAllMessages">Select All</button>
                        <button class="text-btn" @click="deselectAllMessages">Deselect All</button>
                      </div>
                    </div>
                    <div class="messages-list-select">
                      <div
                        v-for="(msg, index) in messages.filter(m => m.role === 'assistant')"
                        :key="index"
                        class="message-select-item"
                        :class="{ selected: selectedMessages.has(messages.indexOf(msg)) }"
                        @click="toggleMessageSelection(messages.indexOf(msg))"
                      >
                        <div class="message-checkbox">
                          <svg v-if="selectedMessages.has(messages.indexOf(msg))" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="20 6 9 17 4 12"/>
                          </svg>
                        </div>
                        <div class="message-preview">
                          {{ msg.content.slice(0, 150) }}{{ msg.content.length > 150 ? '...' : '' }}
                        </div>
                      </div>
                    </div>
                    <div class="selection-count">
                      {{ selectedMessages.size }} message(s) selected
                    </div>
                  </div>
                </div>

                <!-- AI Summary Preview -->
                <div v-if="isSummarizing || showSummaryPreview" class="summary-preview-section">
                  <div class="section-header">
                    <label class="section-label">
                      <span v-if="isSummarizing" class="loading-indicator">
                        <span class="spinner"></span>
                        {{ summarizeProgress }}
                      </span>
                      <span v-else>AI 整理结果</span>
                    </label>
                    <button v-if="isSummarizing" class="text-btn cancel-btn" @click="cancelSummarize">
                      取消
                    </button>
                  </div>
                  <div class="summary-content" :class="{ 'loading': isSummarizing }">
                    <pre v-if="summaryContent">{{ summaryContent }}</pre>
                    <div v-else-if="isSummarizing" class="placeholder">
                      正在生成内容，请稍候...
                    </div>
                  </div>
                </div>

                <div class="dialog-footer">
                  <button class="btn-secondary" @click="closeExportDialog">Cancel</button>
                  <button class="btn-primary" @click="confirmExport" :disabled="selectedMessages.size === 0">
                    Export to Editor
                  </button>
                </div>
              </div>
            </div>
          </Transition>
        </Teleport>
        <div class="panel-header">
          <h3>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            Note Editor
          </h3>
          <div class="panel-actions">
            <button class="action-btn export" @click="exportFromChat" title="Export from chat" :disabled="messages.length === 0">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 5v14M5 12l7 7 7-7"/>
              </svg>
              Export
            </button>
          </div>
        </div>

        <div class="editor-content">
          <!-- Form Fields -->
          <div class="form-section">
            <div class="form-group">
              <label>Title <span class="required">*</span></label>
              <input
                v-model="noteTitle"
                type="text"
                class="form-input"
                placeholder="Enter article title"
                maxlength="64"
              />
            </div>

            <div class="form-row">
              <div class="form-group">
                <label>Theme</label>
                <select v-model="noteTheme" class="form-select">
                  <option value="tech">Tech</option>
                  <option value="minimal">Minimal</option>
                  <option value="business">Business</option>
                </select>
              </div>
              <div class="form-group">
                <label>Author</label>
                <input
                  v-model="noteAuthor"
                  type="text"
                  class="form-input"
                  placeholder="Author name"
                  maxlength="10"
                />
              </div>
            </div>

            <div class="form-group">
              <label>Digest</label>
              <input
                v-model="noteDigest"
                type="text"
                class="form-input"
                placeholder="Brief summary (optional)"
                maxlength="120"
              />
            </div>
          </div>

          <!-- Editor -->
          <div class="editor-section">
            <div class="editor-toolbar">
              <span class="toolbar-label">Content</span>
              <div class="toolbar-actions">
                <button class="toolbar-btn" @click="clearEditor">Clear</button>
                <button class="toolbar-btn" @click="loadExample">Example</button>
              </div>
            </div>
            <textarea
              v-model="noteContent"
              class="note-editor"
              placeholder="Write your article content here using Markdown..."
              spellcheck="false"
            ></textarea>
          </div>

          <!-- Preview -->
          <div v-if="showPreview" class="preview-section">
            <div class="preview-header">
              <span>HTML Preview</span>
              <button class="close-preview" @click="showPreview = false">×</button>
            </div>
            <div class="preview-content" v-html="previewHtml"></div>
          </div>
        </div>

        <!-- Editor Actions -->
        <div class="editor-footer">
          <div class="char-count">{{ noteContent.length }} chars</div>
          <div class="footer-actions">
            <div class="export-dropdown">
              <button class="btn-secondary export-btn" @click="showExportMenu = !showExportMenu" :disabled="!noteContent">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
                </svg>
                Export
                <svg class="dropdown-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>
              <div v-if="showExportMenu" class="export-menu">
                <button class="export-option" @click="exportAs('markdown')">
                  <span>📝</span> Markdown
                </button>
                <button class="export-option" @click="exportAs('html')">
                  <span>🌐</span> HTML
                </button>
                <button class="export-option" @click="exportAs('pdf')">
                  <span>📄</span> PDF
                </button>
              </div>
            </div>
            <button class="btn-secondary" @click="previewArticle" :disabled="isConverting || !noteContent">
              {{ isConverting ? 'Converting...' : 'Preview' }}
            </button>
            <button class="btn-primary" @click="publishArticle" :disabled="isPublishing || !canPublish">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/>
              </svg>
              {{ isPublishing ? 'Publishing...' : 'Publish' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

// Chat state
const messages = ref([])
const userInput = ref('')
const isStreaming = ref(false)
const streamingContent = ref('')
const chatContainer = ref(null)

// Note editor state
const noteTitle = ref('')
const noteAuthor = ref('Paper Agent')
const noteTheme = ref('tech')
const noteDigest = ref('')
const noteContent = ref('')
const isConverting = ref(false)
const isPublishing = ref(false)
const showPreview = ref(false)
const previewHtml = ref('')

// Export dialog state
const showExportDialog = ref(false)
const selectedMessages = ref(new Set())
const selectedTemplate = ref('article')
const isExporting = ref(false)
const isSummarizing = ref(false)  // AI 总结中状态
const showSummaryPreview = ref(false)  // 显示总结预览
const summaryContent = ref('')  // 总结后的内容
const summarizeProgress = ref('')  // 总结进度提示
const showExportMenu = ref(false)

// Export templates
const exportTemplates = [
  { id: 'article', name: '技术文章', icon: '📝', description: '适合技术分享和教程' },
  { id: 'notes', name: '读书笔记', icon: '📚', description: '整理阅读笔记和要点' },
  { id: 'interview', name: '访谈记录', icon: '🎤', description: '问答形式的访谈内容' },
  { id: 'news', name: '新闻简报', icon: '📰', description: '简洁的新闻摘要格式' },
  { id: 'summary', name: '对话总结', icon: '💬', description: '总结对话要点' }
]

// Computed
const canPublish = computed(() => {
  return noteTitle.value && noteContent.value && previewHtml.value
})

// Chat methods
const renderMarkdown = (content) => {
  if (!content) return ''
  return DOMPurify.sanitize(marked.parse(content))
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

const sendQuickMessage = (text) => {
  userInput.value = text
  sendMessage()
}

const sendMessage = async () => {
  const content = userInput.value.trim()
  if (!content || isStreaming.value) return

  // Add user message
  messages.value.push({ role: 'user', content })
  userInput.value = ''
  await scrollToBottom()

  // Start streaming
  isStreaming.value = true
  streamingContent.value = ''

  try {
    // Use fetch to initiate the request with POST body
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: messages.value,
        stream: true // Enable streaming
      })
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Chat failed')
    }

    // Read the stream
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let fullContent = ''
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      buffer += chunk

      // Process complete lines
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' // Keep the last incomplete line

      for (const line of lines) {
        const trimmedLine = line.trim()
        if (trimmedLine.startsWith('data: ')) {
          try {
            const dataStr = trimmedLine.slice(6)
            if (dataStr === '[DONE]') continue

            const data = JSON.parse(dataStr)

            if (data.content) {
              fullContent += data.content
              streamingContent.value = fullContent
              await scrollToBottom()
            }

            if (data.done || data.error) {
              if (data.error) {
                throw new Error(data.error)
              }
            }
          } catch (e) {
            // Ignore parsing errors for non-JSON lines
            console.debug('Parse error:', e)
          }
        }
      }
    }

    // Process any remaining buffer
    if (buffer.trim().startsWith('data: ')) {
      try {
        const dataStr = buffer.trim().slice(6)
        const data = JSON.parse(dataStr)
        if (data.content) {
          fullContent += data.content
        }
      } catch (e) {
        // Ignore
      }
    }

    // Add complete AI message
    messages.value.push({
      role: 'assistant',
      content: fullContent
    })
  } catch (error) {
    console.error('Chat error:', error)
    messages.value.push({
      role: 'assistant',
      content: `Error: ${error.message}. Please try again.`
    })
  } finally {
    isStreaming.value = false
    streamingContent.value = ''
    await scrollToBottom()
  }
}

const clearChat = () => {
  if (confirm('Clear all chat messages?')) {
    messages.value = []
  }
}

const copyMessage = (content) => {
  navigator.clipboard.writeText(content)
}

const exportFromChat = () => {
  // Open export dialog instead of directly exporting
  if (messages.value.filter(m => m.role === 'assistant').length === 0) {
    alert('No AI messages to export')
    return
  }
  // Select all assistant messages by default
  selectedMessages.value = new Set(
    messages.value
      .map((m, index) => ({ ...m, index }))
      .filter(m => m.role === 'assistant')
      .map(m => m.index)
  )
  showExportDialog.value = true
}

const toggleMessageSelection = (index) => {
  const newSet = new Set(selectedMessages.value)
  if (newSet.has(index)) {
    newSet.delete(index)
  } else {
    newSet.add(index)
  }
  selectedMessages.value = newSet
}

const selectAllMessages = () => {
  selectedMessages.value = new Set(
    messages.value
      .map((m, index) => ({ ...m, index }))
      .filter(m => m.role === 'assistant')
      .map(m => m.index)
  )
}

const deselectAllMessages = () => {
  selectedMessages.value = new Set()
}

// 生成专业总结 Prompt
const generateSummaryPrompt = (content, template, title) => {
  const now = new Date().toLocaleDateString('zh-CN')

  switch (template) {
    case 'article':
      return `请将以下对话内容整理成一篇专业的技术文章。

要求：
1. 文章结构：引言 → 核心内容（分小节） → 实践建议 → 总结
2. 为每个小节添加合适的小标题（使用 ## 或 ###）
3. 提取技术概念、原理、应用场景，保持技术准确性
4. 添加关键要点标注（使用 **加粗** 或引用块）
5. 语言风格：专业、清晰、有条理
6. 文章标题：${title || '技术文章'}

原始内容：
${content}

请直接输出整理后的 Markdown 格式文章内容（不需要包含标题 #，因为我会在外层添加）：`

    case 'notes':
      return `请将以下对话内容整理成一份专业的读书笔记。

要求：
1. 提取 3-5 个核心观点或启发
2. 每个观点配简要说明和个人启发（使用引用块格式）
3. 添加「金句摘录」板块，列出值得记住的句子
4. 使用要点列表和引用块增强可读性
5. 记录时间：${now}

原始内容：
${content}

请直接输出整理后的 Markdown 格式笔记内容（不需要包含标题 #）：`

    case 'interview':
      return `请将以下对话内容整理成一份结构化的访谈记录。

要求：
1. 识别问答模式，整理成 Q&A 格式（Q: / A:）
2. 或提取核心观点，按主题分类组织
3. 添加「核心洞察」板块，总结 3-5 个重要观点
4. 保持受访者原意，不添加未提及的内容
5. 使用引用块突出重要言论

原始内容：
${content}

请直接输出整理后的 Markdown 格式访谈记录（不需要包含标题 #）：`

    case 'news':
      return `请将以下对话内容整理成一份简洁的新闻简报。

要求：
1. 包含 5W1H 要素（何时、何地、何人、何事、为何、如何）
2. 使用倒金字塔结构：最重要的信息在前
3. 添加「关键数据/事实」板块，列出具体数字和事实
4. 添加「影响与意义」板块
5. 语言风格：客观、简洁、信息密度高
6. 时间：${now}

原始内容：
${content}

请直接输出整理后的 Markdown 格式新闻简报（不需要包含标题 #）：`

    case 'summary':
      return `请将以下对话内容整理成一份简洁的对话总结。

要求：
1. 提取关键结论和决策（使用 ## 关键结论 标题）
2. 列出行动建议（如有）（使用 ## 行动建议 标题）
3. 添加「遗留问题」板块，列出未解决的问题
4. 语言风格：简洁明了，突出重点
5. 对话时间：${now}

原始内容：
${content}

请直接输出整理后的 Markdown 格式总结内容（不需要包含标题 #）：`

    default:
      return `请总结以下内容：\n\n${content}`
  }
}

// 获取模板标题
const getTemplateTitle = (template) => {
  const titles = {
    article: noteTitle.value || '技术文章',
    notes: noteTitle.value || '阅读笔记',
    interview: noteTitle.value || '访谈记录',
    news: noteTitle.value || '新闻简报',
    summary: noteTitle.value || '对话总结'
  }
  return titles[template] || noteTitle.value
}

// AI 总结函数
const summarizeWithAI = async (content, template) => {
  const prompt = generateSummaryPrompt(content, template, getTemplateTitle(template))

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'user', content: prompt }],
        stream: true
      })
    })

    if (!response.ok) {
      throw new Error('Summary failed')
    }

    // 读取流式响应
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let fullContent = ''
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      buffer += chunk

      // 处理完整的 SSE 行
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        const trimmedLine = line.trim()
        if (trimmedLine.startsWith('data: ')) {
          try {
            const dataStr = trimmedLine.slice(6)
            if (dataStr === '[DONE]') continue

            const data = JSON.parse(dataStr)
            if (data.content) {
              fullContent += data.content
              summaryContent.value = fullContent
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }

    return fullContent
  } catch (error) {
    console.error('Summary error:', error)
    throw error
  }
}

// 降级方案：使用原始内容
const useOriginalContent = (selected) => {
  const now = new Date().toLocaleDateString('zh-CN')
  const combinedContent = selected.map(m => m.content).join('\n\n---\n\n')

  switch (selectedTemplate.value) {
    case 'article':
      return `# ${noteTitle.value || '技术文章'}\n\n${combinedContent}\n\n---\n\n*本文由 Paper Agent 生成*`
    case 'notes':
      return `# ${noteTitle.value || '阅读笔记'}\n\n> 记录时间：${now}\n\n${combinedContent}\n\n---\n\n*读书笔记*`
    case 'interview':
      return `# ${noteTitle.value || '访谈记录'}\n\n${combinedContent}\n\n---\n\n*访谈整理*`
    case 'news':
      return `# ${noteTitle.value || '新闻简报'}\n\n**摘要**：${noteDigest.value || '今日要闻'}\n\n${combinedContent}\n\n---\n\n*来源：AI 整理 | 时间：${now}*`
    case 'summary':
      return `# ${noteTitle.value || '对话总结'}\n\n## 关键要点\n\n${combinedContent}\n\n---\n\n*对话时间：${now}*`
    default:
      return combinedContent
  }
}

const confirmExport = async () => {
  if (selectedMessages.value.size === 0) {
    alert('Please select at least one message')
    return
  }

  // Get selected messages in order
  const selected = messages.value
    .map((m, index) => ({ ...m, index }))
    .filter(m => selectedMessages.value.has(m.index))
    .sort((a, b) => a.index - b.index)

  // Combine original content
  const combinedContent = selected.map(m => m.content).join('\n\n---\n\n')

  // Extract title from first message if not set
  if (!noteTitle.value) {
    const firstMsg = selected[0]
    const lines = firstMsg.content.split('\n').filter(l => l.trim())
    if (lines.length > 0) {
      noteTitle.value = lines[0].replace(/^#+\s*/, '').slice(0, 64)
    }
  }

  // Auto-generate digest
  if (!noteDigest.value) {
    const allLines = combinedContent.split('\n').filter(l => l.trim())
    if (allLines.length > 0) {
      noteDigest.value = allLines[0].slice(0, 120)
    }
  }

  // Start AI summarization
  isSummarizing.value = true
  showSummaryPreview.value = true
  summaryContent.value = ''
  summarizeProgress.value = 'AI 正在整理笔记...'

  try {
    // Call AI to summarize
    const summarizedContent = await summarizeWithAI(combinedContent, selectedTemplate.value)

    // Add template header and footer
    const now = new Date().toLocaleDateString('zh-CN')
    let finalContent = ''

    switch (selectedTemplate.value) {
      case 'article':
        finalContent = `# ${noteTitle.value}\n\n${summarizedContent}\n\n---\n\n*本文由 Paper Agent 智能整理生成*`
        break
      case 'notes':
        finalContent = `# ${noteTitle.value}\n\n> 记录时间：${now}\n\n${summarizedContent}\n\n---\n\n*读书笔记 | Paper Agent 整理*`
        break
      case 'interview':
        finalContent = `# ${noteTitle.value}\n\n${summarizedContent}\n\n---\n\n*访谈整理 | Paper Agent*`
        break
      case 'news':
        finalContent = `# ${noteTitle.value}\n\n**摘要**：${noteDigest.value}\n\n${summarizedContent}\n\n---\n\n*来源：AI 整理 | 时间：${now}*`
        break
      case 'summary':
        finalContent = `# ${noteTitle.value}\n\n${summarizedContent}\n\n---\n\n*对话总结 | 时间：${now}*`
        break
      default:
        finalContent = `# ${noteTitle.value}\n\n${summarizedContent}`
    }

    // Set note content
    noteContent.value = finalContent
    summarizeProgress.value = '整理完成！'

    // Close dialog after a delay
    setTimeout(() => {
      showExportDialog.value = false
      showSummaryPreview.value = false
      isSummarizing.value = false
      selectedMessages.value = new Set()
    }, 1000)

  } catch (error) {
    console.error('Export error:', error)

    // Fallback to original content
    if (confirm('AI 整理失败，是否使用原始内容？')) {
      noteContent.value = useOriginalContent(selected)
      showExportDialog.value = false
      showSummaryPreview.value = false
      isSummarizing.value = false
      selectedMessages.value = new Set()
    } else {
      isSummarizing.value = false
      summarizeProgress.value = '整理失败，请重试'
    }
  }
}

const cancelSummarize = () => {
  isSummarizing.value = false
  showSummaryPreview.value = false
  summaryContent.value = ''
}

// 旧版 applyTemplate 保留作为降级方案
const applyTemplate = (content, template) => {
  const now = new Date().toLocaleDateString('zh-CN')

  switch (template) {
    case 'article':
      return `# ${noteTitle.value || '技术文章'}\n\n${content}\n\n---\n\n*本文由 Paper Agent 生成*`

    case 'notes':
      return `# ${noteTitle.value || '阅读笔记'}\n\n> 记录时间：${now}\n\n## 核心要点\n\n${content.split('\n').map(line => line.trim() ? `- ${line}` : '').join('\n')}\n\n---\n\n*读书笔记*`

    case 'interview':
      return `# ${noteTitle.value || '访谈记录'}\n\n${content.split('\n\n').map((block, i) => {
        if (block.startsWith('Q:') || block.startsWith('问：')) {
          return `**${block}**`
        }
        return `> ${block}`
      }).join('\n\n')}\n\n---\n\n*访谈整理*`

    case 'news':
      const lines = content.split('\n').filter(l => l.trim())
      return `# ${noteTitle.value || '新闻简报'}\n\n**摘要**：${noteDigest.value || lines[0] || '今日要闻'}\n\n## 主要内容\n\n${content}\n\n---\n\n*来源：AI 整理 | 时间：${now}*`

    case 'summary':
      return `# ${noteTitle.value || '对话总结'}\n\n## 关键要点\n\n${content.split('\n').filter(l => l.trim() && (l.includes('：') || l.includes('1.') || l.includes('-'))).slice(0, 10).join('\n')}\n\n## 完整内容\n\n${content}\n\n---\n\n*对话时间：${now}*`

    default:
      return content
  }
}

const closeExportDialog = () => {
  showExportDialog.value = false
  selectedMessages.value = new Set()
}

// Export methods
const exportAs = async (format) => {
  if (!noteContent.value) return

  showExportMenu.value = false

  switch (format) {
    case 'markdown':
      downloadFile(noteContent.value, `${noteTitle.value || 'note'}.md`, 'text/markdown')
      break
    case 'html':
      if (!previewHtml.value) {
        await previewArticle()
      }
      downloadFile(previewHtml.value, `${noteTitle.value || 'note'}.html`, 'text/html')
      break
    case 'pdf':
      await exportPDF()
      break
  }
}

const downloadFile = (content, filename, type) => {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const exportPDF = async () => {
  if (!noteContent.value) return

  try {
    const res = await fetch('/api/wechat/export-pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: noteTitle.value,
        markdown_content: noteContent.value,
        theme: noteTheme.value
      })
    })

    if (!res.ok) throw new Error('PDF export failed')

    const result = await res.json()

    // Download the PDF file
    const pdfRes = await fetch(result.pdf_url)
    const pdfBlob = await pdfRes.blob()
    const url = URL.createObjectURL(pdfBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = result.filename || `${noteTitle.value || 'note'}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  } catch (error) {
    console.error('PDF export failed:', error)
    alert('PDF export failed: ' + error.message)
  }
}

// Editor methods
const clearEditor = () => {
  if (confirm('Clear editor content?')) {
    noteTitle.value = ''
    noteContent.value = ''
    noteDigest.value = ''
    showPreview.value = false
    previewHtml.value = ''
  }
}

const loadExample = () => {
  noteTitle.value = 'Getting Started with AI Research'
  noteAuthor.value = 'Paper Agent'
  noteTheme.value = 'tech'
  noteDigest.value = 'A comprehensive guide to starting your AI research journey'
  noteContent.value = `# Getting Started with AI Research

Artificial Intelligence has revolutionized the way we approach research and problem-solving. In this article, we'll explore the fundamentals of AI research and how you can get started.

## Why AI Research Matters

AI research drives innovation across multiple domains:

- **Healthcare**: Disease diagnosis and drug discovery
- **Finance**: Risk assessment and fraud detection
- **Education**: Personalized learning experiences
- **Environment**: Climate modeling and conservation

## Key Steps to Begin

### 1. Build a Strong Foundation

Start with the basics of:
- Machine Learning algorithms
- Deep Learning architectures
- Data processing techniques

### 2. Stay Updated

Follow top conferences and journals:
- NeurIPS, ICML, ICLR
- arXiv preprints
- Research blogs and newsletters

### 3. Practice with Real Projects

Apply your knowledge through:
- Kaggle competitions
- Open-source contributions
- Personal research projects

## Conclusion

The field of AI research is constantly evolving. By following these steps and maintaining curiosity, you'll be well on your way to making meaningful contributions to the field.

---

*Happy researching!*`
}

const previewArticle = async () => {
  if (!noteContent.value) return
  isConverting.value = true
  try {
    const res = await fetch('/api/wechat/convert', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        markdown_content: noteContent.value,
        theme: noteTheme.value
      })
    })
    if (!res.ok) throw new Error('Conversion failed')
    const result = await res.json()
    previewHtml.value = result.html_content
    showPreview.value = true
  } catch (error) {
    console.error('Preview failed:', error)
    alert('Failed to generate preview: ' + error.message)
  } finally {
    isConverting.value = false
  }
}

const publishArticle = async () => {
  if (!canPublish.value) return
  isPublishing.value = true
  try {
    const res = await fetch('/api/wechat/publish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: noteTitle.value,
        html_content: previewHtml.value,
        author: noteAuthor.value,
        digest: noteDigest.value || undefined
      })
    })
    if (!res.ok) throw new Error('Publish failed')
    const result = await res.json()
    alert('Published to WeChat successfully! Media ID: ' + result.result.media_id)
    showPreview.value = false
  } catch (error) {
    console.error('Publish failed:', error)
    alert('Failed to publish: ' + error.message)
  } finally {
    isPublishing.value = false
  }
}
</script>

<style scoped>
.wechat-studio {
  max-width: 1600px;
  margin: 0 auto;
  animation: fadeInUp var(--transition-slow);
  height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
}

/* Header */
.studio-header {
  margin-bottom: var(--space-4);
  padding: 0 var(--space-4);
}

.page-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
}

.title-accent {
  color: var(--color-success);
}

.page-subtitle {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

/* Studio Content */
.studio-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
  flex: 1;
  min-height: 0;
  padding: 0 var(--space-4) var(--space-4);
}

/* Panels */
.chat-panel,
.editor-panel {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-elevated);
}

.panel-header h3 {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text-primary);
}

.panel-header h3 svg {
  width: 20px;
  height: 20px;
  color: var(--color-accent-primary);
}

.panel-actions {
  display: flex;
  gap: var(--space-2);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: var(--text-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-btn:hover:not(:disabled) {
  border-color: var(--color-border-hover);
  color: var(--color-text-primary);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn.export {
  background: var(--color-accent-glow);
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
}

.action-btn svg {
  width: 14px;
  height: 14px;
}

/* Chat Messages */
.chat-messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-4);
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: var(--color-text-muted);
}

.empty-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-elevated);
  border-radius: var(--radius-xl);
  margin-bottom: var(--space-4);
}

.empty-icon svg {
  width: 40px;
  height: 40px;
  opacity: 0.5;
}

.empty-chat p {
  font-size: var(--text-lg);
  margin-bottom: var(--space-2);
}

.empty-chat .hint {
  font-size: var(--text-sm);
  opacity: 0.7;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.message {
  display: flex;
  gap: var(--space-3);
  max-width: 90%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.assistant {
  align-self: flex-start;
}

.message-avatar {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: var(--color-accent-primary);
  border-color: var(--color-accent-primary);
  color: var(--color-bg-primary);
}

.message-content {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-3) var(--space-4);
  max-width: calc(100% - 48px);
}

.message.user .message-content {
  background: var(--color-accent-glow);
  border-color: var(--color-accent-primary);
}

.message-text {
  font-size: var(--text-sm);
  line-height: 1.6;
  color: var(--color-text-primary);
}

.message-text :deep(p) {
  margin-bottom: var(--space-2);
}

.message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.message-text :deep(code) {
  background: var(--color-bg-primary);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
}

.message-text :deep(pre) {
  background: var(--color-bg-primary);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin: var(--space-2) 0;
}

.message-text :deep(pre code) {
  background: none;
  padding: 0;
}

.message-actions {
  display: flex;
  gap: var(--space-1);
  margin-top: var(--space-2);
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-border);
}

.msg-action {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.msg-action:hover {
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
}

.msg-action svg {
  width: 14px;
  height: 14px;
}

/* Streaming Indicator */
.typing-indicator {
  display: flex;
  gap: 4px;
  margin-top: var(--space-2);
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: var(--color-text-muted);
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1); }
}

/* Chat Input Area */
.chat-input-area {
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-elevated);
  padding: var(--space-4);
}

.input-wrapper {
  position: relative;
  display: flex;
  gap: var(--space-3);
}

.chat-input {
  flex: 1;
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-primary);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: 1.5;
  resize: none;
  outline: none;
}

.chat-input:focus {
  border-color: var(--color-accent-primary);
}

.chat-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.input-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.send-btn {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.send-btn:hover:not(:disabled) {
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
}

.send-btn.active {
  background: var(--color-accent-primary);
  border-color: var(--color-accent-primary);
  color: var(--color-bg-primary);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn svg {
  width: 20px;
  height: 20px;
}

.send-btn svg.spinning {
  animation: spin 1s linear infinite;
}

.quick-actions {
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-3);
  flex-wrap: wrap;
}

.quick-btn {
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  color: var(--color-text-secondary);
  font-size: var(--text-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.quick-btn:hover {
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
}

/* Editor Panel */
.editor-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-4);
}

.form-section {
  margin-bottom: var(--space-4);
}

.form-group {
  margin-bottom: var(--space-3);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}

.form-group label {
  display: block;
  margin-bottom: var(--space-2);
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-text-secondary);
}

.required {
  color: var(--color-error);
}

.form-input,
.form-select {
  width: 100%;
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-primary);
  font-size: var(--text-sm);
  transition: all var(--transition-fast);
}

.form-input:focus,
.form-select:focus {
  outline: none;
  border-color: var(--color-accent-primary);
}

/* Editor Section */
.editor-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 200px;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-2);
}

.toolbar-label {
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-text-secondary);
}

.toolbar-actions {
  display: flex;
  gap: var(--space-2);
}

.toolbar-btn {
  padding: var(--space-1) var(--space-3);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: var(--text-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.toolbar-btn:hover {
  border-color: var(--color-border-hover);
  color: var(--color-text-primary);
}

.note-editor {
  flex: 1;
  min-height: 200px;
  padding: var(--space-4);
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-primary);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: 1.7;
  resize: none;
  outline: none;
}

.note-editor:focus {
  border-color: var(--color-accent-primary);
}

/* Preview Section */
.preview-section {
  margin-top: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) var(--space-4);
  background: var(--color-bg-elevated);
  border-bottom: 1px solid var(--color-border);
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-text-secondary);
}

.close-preview {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  font-size: var(--text-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.close-preview:hover {
  color: var(--color-error);
}

.preview-content {
  padding: var(--space-4);
  max-height: 400px;
  overflow-y: auto;
  background: var(--color-bg-primary);
}

/* Editor Footer */
.editor-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4);
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-elevated);
}

.char-count {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.footer-actions {
  display: flex;
  gap: var(--space-3);
}

.btn-secondary,
.btn-primary {
  padding: var(--space-2) var(--space-4);
  border: none;
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-secondary {
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
}

.btn-secondary:hover:not(:disabled) {
  border-color: var(--color-border-hover);
  color: var(--color-text-primary);
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  background: linear-gradient(135deg, var(--color-success), var(--color-success-hover));
  color: var(--color-bg-primary);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary svg {
  width: 16px;
  height: 16px;
}

/* Export Dropdown */
.export-dropdown {
  position: relative;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.export-btn svg {
  width: 16px;
  height: 16px;
}

.export-btn .dropdown-arrow {
  width: 12px;
  height: 12px;
  transition: transform 0.2s;
}

.export-menu {
  position: absolute;
  bottom: 100%;
  left: 0;
  margin-bottom: var(--space-2);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-2);
  min-width: 160px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 100;
}

.export-option {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-2) var(--space-3);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.export-option:hover {
  background: var(--color-bg-elevated);
}

.export-option span {
  font-size: var(--text-base);
}

/* Export Dialog */
.export-dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--space-4);
}

.export-dialog {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-elevated);
}

.dialog-header h3 {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text-primary);
}

.dialog-header h3 svg {
  width: 20px;
  height: 20px;
  color: var(--color-accent-primary);
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  font-size: var(--text-xl);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.close-btn:hover {
  background: var(--color-bg-primary);
  color: var(--color-error);
}

.dialog-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4);
}

.section-label {
  display: block;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: var(--space-3);
}

/* Template Grid */
.template-section {
  margin-bottom: var(--space-6);
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-3);
}

.template-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4);
  background: var(--color-bg-primary);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.template-card:hover {
  border-color: var(--color-border-hover);
}

.template-card.active {
  border-color: var(--color-accent-primary);
  background: var(--color-accent-glow);
}

.template-icon {
  font-size: var(--text-2xl);
}

.template-name {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-primary);
}

.template-desc {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-align: center;
}

/* Message Selection */
.messages-section {
  margin-bottom: var(--space-4);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-3);
}

.selection-actions {
  display: flex;
  gap: var(--space-2);
}

.text-btn {
  padding: var(--space-1) var(--space-2);
  background: transparent;
  border: none;
  color: var(--color-accent-primary);
  font-size: var(--text-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.text-btn:hover {
  text-decoration: underline;
}

.messages-list-select {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  max-height: 300px;
  overflow-y: auto;
}

.message-select-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3);
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.message-select-item:hover {
  border-color: var(--color-border-hover);
}

.message-select-item.selected {
  border-color: var(--color-accent-primary);
  background: var(--color-accent-glow);
}

.message-checkbox {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-card);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  margin-top: 2px;
}

.message-select-item.selected .message-checkbox {
  background: var(--color-accent-primary);
  border-color: var(--color-accent-primary);
  color: var(--color-bg-primary);
}

.message-checkbox svg {
  width: 14px;
  height: 14px;
}

.message-preview {
  flex: 1;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.selection-count {
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  text-align: center;
}

/* Summary Preview Section */
.summary-preview-section {
  margin-top: var(--space-4);
  padding: var(--space-4);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.summary-preview-section .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-3);
}

.summary-preview-section .section-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: 0;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-accent-primary);
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.cancel-btn {
  color: var(--color-error);
}

.cancel-btn:hover {
  text-decoration: underline;
}

.summary-content {
  max-height: 300px;
  overflow-y: auto;
  padding: var(--space-3);
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.summary-content.loading {
  opacity: 0.7;
}

.summary-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: 1.6;
  color: var(--color-text-primary);
}

.summary-content .placeholder {
  text-align: center;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  padding: var(--space-8);
}

/* Dialog Footer */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4);
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-elevated);
}

/* Dialog Transition */
.dialog-enter-active,
.dialog-leave-active {
  transition: opacity 0.3s ease;
}

.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
}

/* Animations */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Responsive */
@media (max-width: 1024px) {
  .studio-content {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr 1fr;
  }

  .chat-panel,
  .editor-panel {
    min-height: 400px;
  }

  .export-dialog {
    width: 95%;
    max-height: 95vh;
  }
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .quick-actions {
    display: none;
  }

  .footer-actions {
    flex-direction: column;
    gap: var(--space-2);
  }

  .template-grid {
    grid-template-columns: 1fr;
  }
}
</style>
