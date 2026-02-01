<!-- AIMETA P=章节区_章节列表展示|R=章节列表_状态|NR=不含编辑功能|E=component:ChaptersSection|X=ui|A=章节组件|D=vue|S=dom|RD=./README.ai -->
<template>
  <div class="flex flex-col h-full min-h-0 overflow-hidden relative">
    <div class="flex flex-row flex-1 h-full lg:min-h-0 overflow-hidden">
      <!-- 移动端遮罩层 -->
      <div
        v-if="showChapterList"
        class="fixed inset-0 bg-black/50 z-40 lg:hidden"
        @click="showChapterList = false"
      ></div>

      <!-- 章节列表侧边栏 -->
      <aside
        class="fixed lg:static inset-y-0 left-0 z-50 w-72 lg:w-72 bg-[var(--novel-surface-container)] border-r border-[var(--novel-outline-variant)] flex flex-col h-full min-h-0 max-h-full overflow-hidden transition-transform duration-300 lg:translate-x-0 shadow-2xl lg:shadow-none"
        :class="showChapterList ? 'translate-x-0' : '-translate-x-full'"
      >
        <div class="px-5 py-4 border-b border-[var(--novel-outline-variant)] flex items-center justify-between">
          <h3 class="text-base font-semibold text-[var(--novel-on-surface)]">章节</h3>
          <span class="text-xs text-[var(--novel-on-surface-variant)]">{{ chapters.length }} 篇</span>
        </div>
        <ul class="flex-1 h-full overflow-y-auto divide-y divide-[var(--novel-outline-variant)] overscroll-contain">
          <li v-for="(chapter, index) in chapters" :key="chapter.chapter_number">
            <button
              class="w-full text-left px-5 py-3 transition-colors duration-200"
              :class="selectedChapter?.chapter_number === chapter.chapter_number
                ? 'bg-[var(--novel-primary-container)] text-[var(--novel-on-primary-container)] font-semibold'
                : 'hover:bg-[var(--novel-surface-container-low)] text-[var(--novel-on-surface)]'"
              @click="selectChapter(chapter.chapter_number)"
            >
              <div class="flex items-center justify-between gap-3">
                <div class="flex items-center gap-3 min-w-0">
                  <span class="inline-flex items-center justify-center w-6 h-6 text-xs font-semibold text-[var(--novel-on-surface-variant)] bg-[var(--novel-surface-container-high)] rounded-full">
                    {{ index + 1 }}
                  </span>
                  <span class="truncate">{{ chapter.title || `第${chapter.chapter_number}章` }}</span>
                </div>
                <span v-if="chapterCache.has(chapter.chapter_number)" class="text-xs text-[var(--novel-on-surface-variant)] opacity-70">
                  {{ calculateWordCount(chapterCache.get(chapter.chapter_number)?.content) }} 字
                </span>
                <span v-else class="text-xs text-[var(--novel-on-surface-variant)] opacity-70">-</span>
              </div>
              <p v-if="chapter.summary" class="mt-1 text-xs text-[var(--novel-on-surface-variant)] truncate">
                {{ chapter.summary }}
              </p>
            </button>
          </li>
        </ul>
      </aside>

      <section class="flex-1 flex flex-col bg-[var(--novel-surface-bright)] h-full min-h-0 max-h-full overflow-hidden relative">
        <!-- 移动端浮动按钮 -->
        <button
          v-if="!showChapterList"
          @click="showChapterList = true"
          class="lg:hidden fixed bottom-6 left-6 z-30 w-14 h-14 bg-[var(--novel-primary)] text-[var(--novel-on-primary)] rounded-full shadow-lg flex items-center justify-center hover:bg-[var(--novel-primary-light)] transition-colors"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <!-- Loading State -->
        <div v-if="isLoading" class="h-full flex items-center justify-center">
          <div class="text-center">
            <div class="w-10 h-10 border-4 border-[var(--novel-outline-variant)] border-t-[var(--novel-primary)] rounded-full animate-spin mx-auto mb-3"></div>
            <p class="text-sm text-[var(--novel-on-surface-variant)]">加载中...</p>
          </div>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="h-full flex items-center justify-center">
          <div class="text-center">
            <div class="w-12 h-12 bg-[var(--novel-error-container)] rounded-full flex items-center justify-center mx-auto mb-3">
              <svg class="w-6 h-6 text-[var(--novel-error)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p class="text-sm text-[var(--novel-on-surface)]">{{ error }}</p>
          </div>
        </div>

        <!-- Content -->
        <template v-else-if="selectedChapter">
          <!-- Header with Status and Tabs -->
          <header class="px-6 py-4 border-b border-[var(--novel-outline-variant)] bg-[var(--novel-surface-container-low)]">
            <div class="flex items-start justify-between gap-4 mb-3">
              <div class="flex-1">
                <h4 class="text-xl font-bold text-[var(--novel-on-surface)]">{{ selectedChapter.title || `第${selectedChapter.chapter_number}章` }}</h4>
                <div class="flex items-center gap-3 mt-1.5">
                  <span class="text-sm text-[var(--novel-on-surface-variant)]">第 {{ selectedChapter.chapter_number }} 章</span>
                  <span class="text-sm text-[var(--novel-on-surface-variant)] opacity-70">·</span>
                  <span class="text-sm text-[var(--novel-on-surface-variant)]">{{ calculateWordCount(selectedChapter.content) }} 字</span>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <button
                  class="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium rounded-lg border border-[var(--novel-outline-variant)] text-[var(--novel-on-surface)] hover:bg-[var(--novel-surface-container)] transition-colors duration-200"
                  @click="openBatchExportModal"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7h18M3 12h18M3 17h18" />
                  </svg>
                  批量导出
                </button>
                <button
                  class="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors duration-200"
                  :class="selectedChapter?.content
                    ? 'border-[var(--novel-outline-variant)] text-[var(--novel-primary)] hover:bg-[var(--novel-primary-container)]'
                    : 'border-[var(--novel-outline-variant)] text-[var(--novel-on-surface-variant)] opacity-50 cursor-not-allowed'"
                  :disabled="!selectedChapter?.content"
                  @click="exportChapterAsTxt"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v16h16V4m-4 4l-4-4-4 4m4-4v12" />
                  </svg>
                  导出TXT
                </button>
                <button
                  class="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium rounded-lg border transition-colors duration-200"
                  :class="selectedChapter?.content
                    ? 'border-[var(--novel-outline-variant)] text-[var(--novel-primary)] hover:bg-[var(--novel-primary-container)]'
                    : 'border-[var(--novel-outline-variant)] text-[var(--novel-on-surface-variant)] opacity-50 cursor-not-allowed'"
                  :disabled="!selectedChapter?.content"
                  @click="copyChapterContent"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M8 4h10a2 2 0 012 2v12a2 2 0 01-2 2H8a2 2 0 01-2-2V6a2 2 0 012-2zm-4 4h2v14a2 2 0 002 2h10v-2H8a2 2 0 01-2-2V8H4z"
                    />
                  </svg>
                  复制正文
                </button>
                <span v-if="selectedChapter.generation_status"
                  class="px-3 py-1 text-xs font-medium rounded-full"
                  :style="getStatusStyle(selectedChapter.generation_status)">
                  {{ getStatusLabel(selectedChapter.generation_status) }}
                </span>
              </div>
            </div>

            <!-- Tab Navigation -->
            <div class="flex gap-1">
              <button
                v-for="tab in tabs"
                :key="tab.key"
                @click="activeTab = tab.key"
                class="px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200"
                :class="activeTab === tab.key
                  ? 'bg-[var(--novel-surface)] text-[var(--novel-primary)] shadow-sm'
                  : 'text-[var(--novel-on-surface-variant)] hover:text-[var(--novel-on-surface)] hover:bg-[var(--novel-surface)]'"
              >
                {{ tab.label }}
                <span v-if="tab.badge && getTabBadgeCount(tab.key)"
                  class="ml-1.5 px-1.5 py-0.5 text-xs rounded-full"
                  :class="activeTab === tab.key
                    ? 'bg-[var(--novel-primary-container)] text-[var(--novel-primary)]'
                    : 'bg-[var(--novel-surface-container-high)] text-[var(--novel-on-surface-variant)]'">
                  {{ getTabBadgeCount(tab.key) }}
                </span>
              </button>
            </div>
          </header>

          <!-- Tab Content -->
          <article class="flex-1 h-full overflow-y-auto min-h-0 overscroll-contain">
            <!-- 正文 Tab -->
            <div v-show="activeTab === 'content'" class="px-2 py-3">
              <div class="max-w-full space-y-4">
                <!-- Summary Cards -->
                <div v-if="selectedChapter.summary || selectedChapter.real_summary" class="grid gap-4">
                  <div v-if="selectedChapter.summary" class="rounded-xl p-4 border border-[var(--novel-outline-variant)] bg-[var(--novel-info-container)]">
                    <h5 class="text-xs font-semibold text-[var(--novel-on-info-container)] mb-2 flex items-center gap-1.5">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      计划大纲
                    </h5>
                    <p class="text-sm text-[var(--novel-on-info-container)] leading-relaxed">{{ selectedChapter.summary }}</p>
                  </div>
                  <div v-if="selectedChapter.real_summary" class="rounded-xl p-4 border border-[var(--novel-outline-variant)] bg-[var(--novel-success-container)]">
                    <h5 class="text-xs font-semibold text-[var(--novel-on-success-container)] mb-2 flex items-center gap-1.5">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                      </svg>
                      实际内容概要
                    </h5>
                    <div class="prose prose-sm max-w-none m3-summary-prose-success" v-html="renderMarkdown(selectedChapter.real_summary)"></div>
                  </div>
                </div>

                <!-- Main Content -->
                <div class="prose max-w-none p-4 sm:p-6 rounded-xl bg-[var(--novel-surface)] border border-[var(--novel-outline-variant)]">
                  <div class="text-base text-[var(--novel-on-surface)] leading-8 whitespace-pre-wrap" style="font-family: var(--novel-font-serif);">
                    {{ selectedChapter.content || '暂无内容' }}
                  </div>
                </div>
              </div>
            </div>

            <!-- 版本 Tab -->
            <div v-show="activeTab === 'versions'" class="px-2 py-3">
              <div class="max-w-full">
                <div v-if="selectedChapter.versions && selectedChapter.versions.length > 0" class="space-y-4">
                  <div v-for="(version, index) in selectedChapter.versions" :key="index"
                    class="border border-[var(--novel-outline-variant)] bg-[var(--novel-surface)] rounded-xl p-5 hover:border-[var(--novel-primary)] hover:shadow-md transition-all duration-200 group cursor-pointer"
                    @click="openVersionModal(version, index)">
                    <div class="flex items-center justify-between mb-3">
                      <h5 class="text-sm font-semibold text-[var(--novel-on-surface)] flex items-center gap-2">
                        <span class="w-6 h-6 bg-[var(--novel-primary-container)] text-[var(--novel-primary)] rounded-full flex items-center justify-center text-xs font-bold">
                          {{ index + 1 }}
                        </span>
                        版本 {{ index + 1 }}
                      </h5>
                      <div class="flex items-center gap-3">
                        <span class="text-xs text-[var(--novel-on-surface-variant)]">{{ calculateWordCount(version) }} 字</span>
                        <span class="text-xs font-medium text-[var(--novel-primary)] opacity-0 group-hover:opacity-100 transition-opacity">
                          点击查看全文 →
                        </span>
                      </div>
                    </div>
                    <div class="text-sm text-[var(--novel-on-surface)] leading-7 whitespace-pre-wrap line-clamp-4">
                      {{ version }}
                    </div>
                  </div>
                </div>
                <div v-else class="text-center py-12 text-[var(--novel-on-surface-variant)]">
                  暂无版本记录
                </div>
              </div>
            </div>

            <!-- 评审 Tab -->
            <div v-show="activeTab === 'evaluation'" class="px-2 py-3">
              <div class="max-w-full">
                <div v-if="evaluationData" class="space-y-4">
                  <!-- 最佳选择 -->
                  <div v-if="evaluationData.best_choice" class="bg-[var(--novel-primary-container)] border border-[var(--novel-outline-variant)] rounded-xl p-4">
                    <div class="flex items-start gap-4">
                      <div class="w-12 h-12 bg-[var(--novel-primary)] rounded-xl flex items-center justify-center flex-shrink-0">
                        <svg class="w-7 h-7 text-[var(--novel-on-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                        </svg>
                      </div>
                      <div class="flex-1">
                        <h5 class="text-lg font-bold text-[var(--novel-on-primary-container)] mb-2">最佳版本选择</h5>
                        <div class="flex items-center gap-2 mb-3">
                          <span class="px-3 py-1 bg-[var(--novel-primary)] text-[var(--novel-on-primary)] text-sm font-bold rounded-full">
                            版本 {{ evaluationData.best_choice }}
                          </span>
                        </div>
                        <p v-if="evaluationData.reason_for_choice" class="text-sm text-[var(--novel-on-primary-container)] leading-relaxed">
                          {{ evaluationData.reason_for_choice }}
                        </p>
                      </div>
                    </div>
                  </div>

                  <!-- 各版本详细评审 -->
                  <div v-if="evaluationData.evaluation" class="space-y-4">
                    <div v-for="(versionEval, versionKey) in evaluationData.evaluation" :key="versionKey"
                      class="border border-[var(--novel-outline-variant)] rounded-xl overflow-hidden"
                      :class="isSelectedVersion(versionKey, evaluationData.best_choice) ? 'ring-2 ring-[var(--novel-primary)]' : ''">
                      <!-- 版本标题 -->
                      <div class="px-5 py-3 bg-[var(--novel-surface-container-low)] border-b border-[var(--novel-outline-variant)] flex items-center justify-between">
                        <h6 class="font-bold text-[var(--novel-on-surface)] flex items-center gap-2">
                          <span class="w-6 h-6 bg-[var(--novel-primary)] text-[var(--novel-on-primary)] rounded-full flex items-center justify-center text-xs">
                            {{ getVersionNumber(versionKey) }}
                          </span>
                          {{ getVersionLabel(versionKey) }}
                        </h6>
                        <span v-if="isSelectedVersion(versionKey, evaluationData.best_choice)"
                          class="px-2.5 py-1 bg-[var(--novel-primary-container)] text-[var(--novel-on-primary-container)] text-xs font-semibold rounded-full">
                          最佳
                        </span>
                      </div>

                      <div class="p-4 space-y-3">
                        <!-- 优点 -->
                        <div v-if="versionEval.pros && versionEval.pros.length > 0"
                          class="bg-[var(--novel-success-container)] border border-[var(--novel-outline-variant)] rounded-lg p-3">
                          <h6 class="text-xs font-bold text-[var(--novel-on-success-container)] mb-2 flex items-center gap-1.5">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            优点
                          </h6>
                          <ul class="space-y-1.5">
                            <li v-for="(item, idx) in versionEval.pros" :key="idx"
                              class="flex items-start gap-2 text-xs text-[var(--novel-on-success-container)] leading-relaxed">
                              <span class="w-1 h-1 bg-[var(--novel-success)] rounded-full mt-1.5 flex-shrink-0"></span>
                              <span>{{ item }}</span>
                            </li>
                          </ul>
                        </div>

                        <!-- 缺点 -->
                        <div v-if="versionEval.cons && versionEval.cons.length > 0"
                          class="bg-[var(--novel-error-container)] border border-[var(--novel-outline-variant)] rounded-lg p-3">
                          <h6 class="text-xs font-bold text-[var(--novel-on-error-container)] mb-2 flex items-center gap-1.5">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                            缺点
                          </h6>
                          <ul class="space-y-1.5">
                            <li v-for="(item, idx) in versionEval.cons" :key="idx"
                              class="flex items-start gap-2 text-xs text-[var(--novel-on-error-container)] leading-relaxed">
                              <span class="w-1 h-1 bg-[var(--novel-error)] rounded-full mt-1.5 flex-shrink-0"></span>
                              <span>{{ item }}</span>
                            </li>
                          </ul>
                        </div>

                        <!-- 总体评价 -->
                        <div v-if="versionEval.overall_review"
                          class="bg-[var(--novel-info-container)] border border-[var(--novel-outline-variant)] rounded-lg p-3">
                          <h6 class="text-xs font-bold text-[var(--novel-on-info-container)] mb-2">总体评价</h6>
                          <p class="text-xs text-[var(--novel-on-info-container)] leading-relaxed">{{ versionEval.overall_review }}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- 简单格式兼容 -->
                  <div v-else-if="evaluationData.decision || evaluationData.feedback" class="space-y-4">
                    <!-- 评审决策 -->
                    <div v-if="evaluationData.decision" class="bg-[var(--novel-info-container)] border border-[var(--novel-outline-variant)] rounded-xl p-4">
                      <div class="flex items-center gap-3 mb-4">
                        <div class="w-10 h-10 bg-[var(--novel-info)] rounded-lg flex items-center justify-center">
                          <svg class="w-6 h-6 text-[var(--novel-on-info)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                        <div>
                          <h5 class="text-sm font-bold text-[var(--novel-on-info-container)]">评审决策</h5>
                          <p class="text-xs text-[var(--novel-on-info-container)] opacity-90">{{ evaluationData.decision }}</p>
                        </div>
                      </div>
                    </div>

                    <!-- 评分卡片 -->
                    <div v-if="evaluationData.scores" class="grid grid-cols-2 md:grid-cols-3 gap-4">
                      <div v-for="(score, key) in evaluationData.scores" :key="key"
                        class="bg-[var(--novel-surface)] border border-[var(--novel-outline-variant)] rounded-xl p-4 hover:shadow-md transition-shadow">
                        <div class="flex items-center justify-between mb-2">
                          <span class="text-xs font-medium text-[var(--novel-on-surface-variant)]">{{ getScoreLabel(key) }}</span>
                          <span class="text-lg font-bold" :class="getScoreColor(score)">{{ score }}</span>
                        </div>
                        <div class="w-full bg-[var(--novel-surface-container-high)] rounded-full h-2">
                          <div class="h-2 rounded-full transition-all duration-300"
                            :class="getScoreBarColor(score)"
                            :style="{ width: `${(score / 10) * 100}%` }"></div>
                        </div>
                      </div>
                    </div>

                    <!-- 详细反馈 -->
                    <div v-if="evaluationData.feedback"
                      class="bg-[var(--novel-surface-container-low)] border border-[var(--novel-outline-variant)] rounded-xl p-4">
                      <h5 class="text-sm font-bold text-[var(--novel-on-surface)] mb-3">详细反馈</h5>
                      <p class="text-sm text-[var(--novel-on-surface)] leading-relaxed whitespace-pre-wrap">{{ evaluationData.feedback }}</p>
                    </div>
                  </div>
                </div>

                <div v-else class="text-center py-12">
                  <div class="w-16 h-16 bg-[var(--novel-surface-container-high)] rounded-full flex items-center justify-center mx-auto mb-3">
                    <svg class="w-8 h-8 text-[var(--novel-on-surface-variant)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <p class="text-[var(--novel-on-surface-variant)]">暂无评审意见</p>
                </div>
              </div>
            </div>
          </article>
        </template>

        <!-- Empty State -->
        <div v-else class="h-full flex items-center justify-center text-[var(--novel-on-surface-variant)]">
          <div class="text-center">
            <svg class="w-16 h-16 mx-auto mb-3 text-[var(--novel-on-surface-variant)] opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            <p class="text-sm">请选择章节查看详细内容</p>
          </div>
        </div>
      </section>
    </div>

    <!-- 批量导出弹窗 -->
    <transition
      enter-active-class="transition-all duration-300"
      leave-active-class="transition-all duration-300"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="showBatchExportModal"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
        @click="closeBatchExportModal"
      >
        <div
          class="bg-[var(--novel-surface)] rounded-2xl shadow-2xl max-w-3xl w-full max-h-[85vh] overflow-hidden"
          @click.stop
        >
          <!-- Modal Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-[var(--novel-outline-variant)] bg-[var(--novel-surface-container-low)]">
            <div>
              <h3 class="text-lg font-bold text-[var(--novel-on-surface)]">批量导出</h3>
              <p class="text-xs text-[var(--novel-on-surface-variant)]">选择要导出的章节</p>
            </div>
            <button
              @click="closeBatchExportModal"
              class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-[var(--novel-surface-container-high)] transition-colors"
            >
              <svg class="w-5 h-5 text-[var(--novel-on-surface-variant)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Modal Content -->
          <div class="overflow-y-auto p-6 max-h-[calc(85vh-10rem)]">
            <div class="space-y-4">
              <div class="flex items-center justify-between gap-3 px-3 py-2 rounded-xl border border-[var(--novel-outline-variant)] bg-[var(--novel-surface-container-low)]">
                <label class="flex items-center gap-2 text-sm text-[var(--novel-on-surface)]">
                  <input
                    ref="selectAllRef"
                    type="checkbox"
                    class="h-4 w-4 rounded border-[var(--novel-outline)] text-[var(--novel-primary)] focus:ring-[var(--novel-primary)] disabled:opacity-50"
                    :disabled="selectableChapterNumbers.length === 0 || isBatchExporting"
                    :checked="isAllSelected"
                    @change="toggleSelectAll"
                  />
                  全选有内容章节
                </label>
                <div class="flex items-center gap-2">
                  <button
                    type="button"
                    class="px-2.5 py-1 text-xs font-medium rounded-lg border border-[var(--novel-outline-variant)] text-[var(--novel-on-surface)] hover:bg-[var(--novel-surface-container-high)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    :disabled="selectableChapterNumbers.length === 0 || isBatchExporting"
                    @click="invertSelection"
                  >
                    反选
                  </button>
                  <span class="text-xs text-[var(--novel-on-surface-variant)]">可选 {{ selectableChapterNumbers.length }} 章</span>
                </div>
              </div>
            </div>
            <div class="space-y-3 mt-3">
              <div
                v-for="chapter in chapters"
                :key="chapter.chapter_number"
                class="flex items-start gap-3 p-3 rounded-xl border border-[var(--novel-outline-variant)] hover:border-[var(--novel-outline)] transition-colors"
                :class="hasChapterContent(chapter) ? 'bg-[var(--novel-surface)]' : 'bg-[var(--novel-surface-container-low)] opacity-70'"
              >
                <input
                  type="checkbox"
                  class="mt-1 h-4 w-4 rounded border-[var(--novel-outline)] text-[var(--novel-primary)] focus:ring-[var(--novel-primary)] disabled:opacity-50"
                  :disabled="!hasChapterContent(chapter) || isBatchExporting"
                  :checked="selectedForExport.includes(chapter.chapter_number)"
                  @change="toggleBatchExportSelection(chapter)"
                />
                <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between gap-3">
                    <span class="text-sm font-medium text-[var(--novel-on-surface)] truncate">
                      第 {{ chapter.chapter_number }} 章：{{ chapter.title || `第${chapter.chapter_number}章` }}
                    </span>
                    <span class="text-xs text-[var(--novel-on-surface-variant)] opacity-70 whitespace-nowrap">
                      {{ chapter.word_count ?? 0 }} 字
                    </span>
                  </div>
                  <p v-if="!hasChapterContent(chapter)" class="text-xs text-[var(--novel-on-surface-variant)] opacity-70 mt-1">
                    无内容，无法导出
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Modal Footer -->
          <div class="flex items-center justify-between px-6 py-4 border-t border-[var(--novel-outline-variant)] bg-[var(--novel-surface-container-low)]">
            <span class="text-sm text-[var(--novel-on-surface-variant)]">已选 {{ selectedForExport.length }} 章</span>
            <div class="flex items-center gap-3">
              <button
                @click="closeBatchExportModal"
                class="px-4 py-2 text-sm font-medium rounded-lg border border-[var(--novel-outline-variant)] text-[var(--novel-on-surface)] hover:bg-[var(--novel-surface-container-high)] transition-colors"
                :disabled="isBatchExporting"
              >
                取消
              </button>
              <button
                @click="exportSelectedChapters"
                class="px-4 py-2 text-sm font-medium rounded-lg bg-[var(--novel-primary)] text-[var(--novel-on-primary)] hover:bg-[var(--novel-primary-light)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                :disabled="selectedForExport.length === 0 || isBatchExporting"
              >
                {{ isBatchExporting ? '导出中...' : '导出选中' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 版本全文弹窗 -->
    <transition
      enter-active-class="transition-all duration-300"
      leave-active-class="transition-all duration-300"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div v-if="versionModal.show" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
        @click="closeVersionModal">
        <div class="bg-[var(--novel-surface)] rounded-2xl shadow-2xl max-w-4xl w-full max-h-[85vh] overflow-hidden"
          @click.stop>
          <!-- Modal Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-[var(--novel-outline-variant)] bg-[var(--novel-surface-container-low)]">
            <div class="flex items-center gap-3">
              <span class="w-8 h-8 bg-[var(--novel-primary)] text-[var(--novel-on-primary)] rounded-full flex items-center justify-center text-sm font-bold">
                {{ versionModal.index + 1 }}
              </span>
              <div>
                <h3 class="text-lg font-bold text-[var(--novel-on-surface)]">版本 {{ versionModal.index + 1 }}</h3>
                <p class="text-xs text-[var(--novel-on-surface-variant)]">{{ calculateWordCount(versionModal.content) }} 字</p>
              </div>
            </div>
            <button @click="closeVersionModal"
              class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-[var(--novel-surface-container-high)] transition-colors">
              <svg class="w-5 h-5 text-[var(--novel-on-surface-variant)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Modal Content -->
          <div class="overflow-y-auto p-6 max-h-[calc(85vh-5rem)]">
            <div class="prose max-w-none">
              <div class="text-base text-[var(--novel-on-surface)] leading-8 whitespace-pre-wrap" style="font-family: var(--novel-font-serif);">
                {{ versionModal.content }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, defineProps, ref, watch, watchEffect } from 'vue'
import { NovelAPI } from '@/api/novel'
import { AdminAPI } from '@/api/admin'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import { copyTextToClipboard } from '@/utils/clipboard'
import { useMessage } from 'naive-ui'

interface ChapterItem {
  chapter_number: number
  title?: string | null
  summary?: string | null
  content?: string | null
  word_count?: number
}

interface ChapterDetail extends ChapterItem {
  real_summary?: string | null
  versions?: string[] | null
  evaluation?: string | null
  generation_status?: string
}

const props = defineProps<{
  chapters: ChapterItem[]
  isAdmin?: boolean
}>()

const route = useRoute()
const projectId = route.params.id as string

const selectedChapter = ref<ChapterDetail | null>(null)
const isLoading = ref(false)
const error = ref<string | null>(null)
const activeTab = ref<'content' | 'versions' | 'evaluation'>('content')
const message = useMessage()

// 移动端章节列表显示状态
const showChapterList = ref(false)

// 批量导出弹窗状态
const showBatchExportModal = ref(false)
const selectedForExport = ref<number[]>([])
const isBatchExporting = ref(false)
const selectAllRef = ref<HTMLInputElement | null>(null)

// 版本弹窗状态
const versionModal = ref({
  show: false,
  content: '',
  index: 0
})

// 缓存已加载的章节详情
const chapterCache = new Map<number, ChapterDetail>()

const chapters = computed(() => props.chapters || [])

// Tab 配置
const tabs = [
  { key: 'content' as const, label: '正文', badge: false },
  { key: 'versions' as const, label: '版本', badge: true },
  { key: 'evaluation' as const, label: '评审', badge: false }
]

// 计算字数的辅助函数
const calculateWordCount = (content: string | null | undefined): number => {
  if (!content) return 0
  // 移除所有空白字符后计算字数
  return content.replace(/\s/g, '').length
}

// 获取状态标签
const getStatusLabel = (status: string): string => {
  const statusMap: Record<string, string> = {
    'not_generated': '未生成',
    'generating': '生成中',
    'evaluating': '评审中',
    'selecting': '选择中',
    'failed': '生成失败',
    'evaluation_failed': '评审失败',
    'waiting_for_confirm': '待确认',
    'successful': '已完成'
  }
  return statusMap[status] || status
}

// 获取状态样式（基于主题 token，避免 Tailwind 固定色导致暗色模式对比度问题）
const getStatusStyle = (status: string): Record<string, string> => {
  const map: Record<string, { bg: string; fg: string }> = {
    not_generated: { bg: 'var(--novel-surface-container-high)', fg: 'var(--novel-on-surface-variant)' },
    generating: { bg: 'var(--novel-info-container)', fg: 'var(--novel-on-info-container)' },
    evaluating: { bg: 'var(--novel-info-container)', fg: 'var(--novel-on-info-container)' },
    selecting: { bg: 'var(--novel-warning-container)', fg: 'var(--novel-on-warning-container)' },
    failed: { bg: 'var(--novel-error-container)', fg: 'var(--novel-on-error-container)' },
    evaluation_failed: { bg: 'var(--novel-error-container)', fg: 'var(--novel-on-error-container)' },
    waiting_for_confirm: { bg: 'var(--novel-warning-container)', fg: 'var(--novel-on-warning-container)' },
    successful: { bg: 'var(--novel-success-container)', fg: 'var(--novel-on-success-container)' }
  }
  const pair = map[status] ?? map.not_generated
  return { backgroundColor: pair.bg, color: pair.fg }
}

// 获取 Tab Badge 数量
const getTabBadgeCount = (tabKey: string): number => {
  if (!selectedChapter.value) return 0
  if (tabKey === 'versions') {
    return selectedChapter.value.versions?.length || 0
  }
  return 0
}

const sanitizeFileName = (name: string): string => {
  return name.replace(/[\\/:*?"<>|]/g, '_')
}

const cleanVersionContent = (content: string): string => {
  if (!content) return ''
  try {
    const parsed = JSON.parse(content)
    const extractContent = (value: any): string | null => {
      if (!value) return null
      if (typeof value === 'string') return value
      if (Array.isArray(value)) {
        for (const item of value) {
          const nested = extractContent(item)
          if (nested) return nested
        }
        return null
      }
      if (typeof value === 'object') {
        for (const key of ['content', 'chapter_content', 'chapter_text', 'text', 'body', 'story']) {
          if (value[key]) {
            const nested = extractContent(value[key])
            if (nested) return nested
          }
        }
      }
      return null
    }
    const extracted = extractContent(parsed)
    if (extracted) {
      content = extracted
    }
  } catch (error) {
    // not a json
  }
  let cleaned = content.replace(/^"|"$/g, '')
  cleaned = cleaned.replace(/\\n/g, '\n')
  cleaned = cleaned.replace(/\\"/g, '"')
  cleaned = cleaned.replace(/\\t/g, '\t')
  cleaned = cleaned.replace(/\\\\/g, '\\')
  return cleaned
}

const buildChapterFileName = (chapterNumber: number, title?: string | null): string => {
  const numberLabel = `第${chapterNumber}章`
  const trimmedTitle = title?.trim() || '无标题'
  const baseName = trimmedTitle === numberLabel ? numberLabel : `${numberLabel} ${trimmedTitle}`
  const safeTitle = sanitizeFileName(baseName) || `chapter-${chapterNumber}`
  return `${safeTitle}.txt`
}

const downloadTxt = (content: string, filename: string) => {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const exportChapterAsTxt = () => {
  const chapter = selectedChapter.value
  if (!chapter) return

  const content = cleanVersionContent(chapter.content ?? '')
  const filename = buildChapterFileName(chapter.chapter_number, chapter.title)
  downloadTxt(content, filename)
}

const copyChapterContent = async () => {
  const chapter = selectedChapter.value
  if (!chapter) return

  const content = cleanVersionContent(chapter.content ?? '')
  if (!content.trim()) {
    message.error('没有可复制的内容')
    return
  }

  const ok = await copyTextToClipboard(content)
  if (!ok) {
    message.error('复制失败：当前环境不支持剪切板')
    return
  }
  message.success('正文已复制到剪切板')
}

const hasChapterContent = (chapter: ChapterItem): boolean => {
  return (chapter.word_count ?? 0) > 0
}

const selectableChapterNumbers = computed(() => {
  return chapters.value.filter(hasChapterContent).map(chapter => chapter.chapter_number)
})

const isAllSelected = computed(() => {
  if (selectableChapterNumbers.value.length === 0) return false
  return selectableChapterNumbers.value.every(number => selectedForExport.value.includes(number))
})

const isSomeSelected = computed(() => {
  if (selectableChapterNumbers.value.length === 0) return false
  return selectedForExport.value.some(number => selectableChapterNumbers.value.includes(number))
})

watchEffect(() => {
  if (selectAllRef.value) {
    selectAllRef.value.indeterminate = isSomeSelected.value && !isAllSelected.value
  }
})

const openBatchExportModal = () => {
  selectedForExport.value = []
  showBatchExportModal.value = true
}

const closeBatchExportModal = () => {
  showBatchExportModal.value = false
}

const toggleBatchExportSelection = (chapter: ChapterItem) => {
  if (!hasChapterContent(chapter)) return
  const chapterNumber = chapter.chapter_number
  const index = selectedForExport.value.indexOf(chapterNumber)
  if (index > -1) {
    selectedForExport.value.splice(index, 1)
  } else {
    selectedForExport.value.push(chapterNumber)
  }
}

const toggleSelectAll = () => {
  if (isAllSelected.value) {
    const selectableSet = new Set(selectableChapterNumbers.value)
    selectedForExport.value = selectedForExport.value.filter(number => !selectableSet.has(number))
    return
  }
  const unique = new Set(selectedForExport.value)
  for (const number of selectableChapterNumbers.value) {
    unique.add(number)
  }
  selectedForExport.value = Array.from(unique)
}

const invertSelection = () => {
  const currentSet = new Set(selectedForExport.value)
  const nextSelection: number[] = []
  for (const number of selectableChapterNumbers.value) {
    if (!currentSet.has(number)) {
      nextSelection.push(number)
    }
  }
  selectedForExport.value = nextSelection
}

const fetchChapterDetail = async (chapterNumber: number): Promise<ChapterDetail | null> => {
  if (chapterCache.has(chapterNumber)) {
    return chapterCache.get(chapterNumber)!
  }
  try {
    const detail: ChapterDetail = props.isAdmin
      ? await AdminAPI.getNovelChapter(projectId, chapterNumber)
      : await NovelAPI.getChapter(projectId, chapterNumber)
    chapterCache.set(chapterNumber, detail)
    return detail
  } catch (err) {
    console.error('加载章节详情失败:', err)
    return null
  }
}

const exportSelectedChapters = async () => {
  if (isBatchExporting.value) return
  if (selectedForExport.value.length === 0) return
  isBatchExporting.value = true
  let skipped = 0

  try {
    const selection = [...selectedForExport.value].sort((a, b) => a - b)
    for (const chapterNumber of selection) {
      const detail = await fetchChapterDetail(chapterNumber)
      const content = cleanVersionContent(detail?.content ?? '')
      if (!content.trim()) {
        skipped += 1
        continue
      }
      const filename = buildChapterFileName(chapterNumber, detail?.title)
      downloadTxt(content, filename)
    }
  } finally {
    isBatchExporting.value = false
  }

  if (skipped > 0) {
    alert(`有 ${skipped} 章无内容已跳过`)
  }
  closeBatchExportModal()
}

// 打开版本弹窗
const openVersionModal = (content: string, index: number) => {
  versionModal.value = {
    show: true,
    content,
    index
  }
}

// 关闭版本弹窗
const closeVersionModal = () => {
  versionModal.value.show = false
}

// 解析评审数据
const evaluationData = computed(() => {
  if (!selectedChapter.value?.evaluation) return null

  try {
    // 尝试解析 JSON
    const parsed = JSON.parse(selectedChapter.value.evaluation)
    return parsed
  } catch {
    // 如果不是 JSON，返回简单的文本格式
    return {
      feedback: selectedChapter.value.evaluation
    }
  }
})

// 获取评分标签
const getScoreLabel = (key: string | number): string => {
  const normalizedKey = typeof key === 'number' ? key.toString() : key
  const labelMap: Record<string, string> = {
    'plot': '情节',
    'character': '人物',
    'writing': '文笔',
    'logic': '逻辑',
    'emotion': '情感',
    'creativity': '创意',
    'coherence': '连贯性',
    'engagement': '吸引力'
  }
  return labelMap[normalizedKey] || normalizedKey
}

// 获取评分颜色
const getScoreColor = (score: number): string => {
  if (score >= 8) return 'text-[var(--novel-success)]'
  if (score >= 6) return 'text-[var(--novel-info)]'
  if (score >= 4) return 'text-[var(--novel-warning)]'
  return 'text-[var(--novel-error)]'
}

// 获取评分条颜色
const getScoreBarColor = (score: number): string => {
  if (score >= 8) return 'bg-[var(--novel-success)]'
  if (score >= 6) return 'bg-[var(--novel-info)]'
  if (score >= 4) return 'bg-[var(--novel-warning)]'
  return 'bg-[var(--novel-error)]'
}

// 从版本 key 中提取版本号 (version1 -> 1)
const getVersionNumber = (versionKey: string | number): number => {
  const normalizedKey = typeof versionKey === 'number' ? versionKey.toString() : versionKey
  const match = normalizedKey.match(/\d+/)
  return match ? parseInt(match[0]) : 0
}

// 获取版本标签
const getVersionLabel = (versionKey: string | number): string => {
  const num = getVersionNumber(versionKey)
  return `版本 ${num}`
}

// 判断是否为选中的版本
const isSelectedVersion = (versionKey: string | number, bestChoice?: number): boolean => {
  if (!bestChoice) return false
  return getVersionNumber(versionKey) === bestChoice
}

// 渲染 Markdown
const renderMarkdown = (text: string | null | undefined): string => {
  if (!text) return ''
  try {
    return marked.parse(text, { breaks: true }) as string
  } catch (error) {
    console.error('Markdown 渲染失败:', error)
    return text
  }
}

// 加载章节详情
const loadChapterDetail = async (chapterNumber: number) => {
  // 检查缓存
  if (chapterCache.has(chapterNumber)) {
    selectedChapter.value = chapterCache.get(chapterNumber)!
    return
  }

  isLoading.value = true
  error.value = null

  try {
    const detail: ChapterDetail = props.isAdmin
      ? await AdminAPI.getNovelChapter(projectId, chapterNumber)
      : await NovelAPI.getChapter(projectId, chapterNumber)

    // 存入缓存
    chapterCache.set(chapterNumber, detail)
    selectedChapter.value = detail
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
    console.error('加载章节详情失败:', err)
  } finally {
    isLoading.value = false
  }
}

watch(
  chapters,
  async (list) => {
    if (list.length === 0) {
      selectedChapter.value = null
      return
    }
    // 自动选中第一个章节（但不加载详情，等用户点击）
    if (!selectedChapter.value && list.length > 0) {
      await loadChapterDetail(list[0].chapter_number)
    }
  },
  { immediate: true }
)

const selectChapter = async (chapterNumber: number) => {
  activeTab.value = 'content' // 切换章节时重置到正文标签
  await loadChapterDetail(chapterNumber)
  // 移动端选择章节后关闭章节列表
  showChapterList.value = false
}

const isAdmin = computed(() => props.isAdmin ?? false)

defineExpose({
  focusChapter: async (chapterNumber: number) => {
    const target = chapters.value.find(ch => ch.chapter_number === chapterNumber)
    if (target) {
      await loadChapterDetail(chapterNumber)
    }
  }
})
</script>

<style scoped>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-4 {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-6 {
  display: -webkit-box;
  -webkit-line-clamp: 6;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* v-html 的 Markdown 内容需要 :deep() 才能命中（避免 scoped CSS 失效） */
.m3-summary-prose-success {
  color: var(--novel-on-success-container);
}

.m3-summary-prose-success :deep(*) {
  color: inherit;
}

.m3-summary-prose-success :deep(a) {
  color: var(--novel-success);
}

.m3-summary-prose-success :deep(li::marker) {
  color: inherit;
  opacity: 0.85;
}
</style>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'ChaptersSection'
})
</script>
