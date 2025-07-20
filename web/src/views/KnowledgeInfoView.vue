<template>
  <div class="knowledge-info-container layout-container">
    <HeaderComponent title="知识项详情" :loading="state.loading">
      <template #actions>
        <a-button @click="goBack">返回</a-button>
        <a-button type="primary" @click="state.openAddContentModal=true">
          添加内容
        </a-button>
      </template>
    </HeaderComponent>

    <div v-if="knowledgeInfo" class="knowledge-info">
      <div class="info-section">
        <h2>{{ knowledgeInfo.name }}</h2>
        <p class="description">{{ knowledgeInfo.description || '暂无描述' }}</p>
        <div class="tags">
          <a-tag color="blue" v-if="knowledgeInfo.type">{{ knowledgeInfo.type }}</a-tag>
          <a-tag color="green" v-if="knowledgeInfo.status">{{ knowledgeInfo.status }}</a-tag>
        </div>
      </div>

      <div class="content-section">
        <h3>知识内容</h3>
        <div class="content-list">
          <div
            v-for="content in knowledgeContents"
            :key="content.id"
            class="content-item"
            @click="viewContent(content)">
            <div class="content-icon">
              <component :is="getContentIcon(content.type)" />
            </div>
            <div class="content-info">
              <h4>{{ content.title }}</h4>
              <p>{{ content.description || '暂无描述' }}</p>
              <div class="content-meta">
                <span>{{ content.type }}</span>
                <span>{{ formatDate(content.created_at) }}</span>
              </div>
            </div>
            <div class="content-actions">
              <a-button size="small" @click.stop="editContent(content)">编辑</a-button>
              <a-button size="small" danger @click.stop="deleteContent(content.id)">删除</a-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加内容模态框 -->
    <a-modal :open="state.openAddContentModal" title="添加知识内容" @ok="addContent" @cancel="cancelAddContent" class="add-content-modal">
      <h3>内容标题<span style="color: var(--error-color)">*</span></h3>
      <a-input v-model:value="newContent.title" placeholder="内容标题" />
      <h3>内容类型</h3>
      <a-select v-model:value="newContent.type" :options="contentTypeOptions" style="width: 100%;" />
      <h3>内容描述</h3>
      <a-textarea
        v-model:value="newContent.description"
        placeholder="内容描述"
        :auto-size="{ minRows: 3, maxRows: 6 }"
      />
      <h3>内容数据</h3>
      <a-textarea
        v-model:value="newContent.data"
        placeholder="请输入内容数据（文本、链接、JSON等）"
        :auto-size="{ minRows: 5, maxRows: 10 }"
      />
      <template #footer>
        <a-button key="back" @click="cancelAddContent">取消</a-button>
        <a-button key="submit" type="primary" :loading="state.adding" @click="addContent">添加</a-button>
      </template>
    </a-modal>

    <!-- 编辑内容模态框 -->
    <a-modal :open="state.openEditContentModal" title="编辑知识内容" @ok="updateContent" @cancel="cancelEditContent" class="edit-content-modal">
      <h3>内容标题<span style="color: var(--error-color)">*</span></h3>
      <a-input v-model:value="editingContent.title" placeholder="内容标题" />
      <h3>内容类型</h3>
      <a-select v-model:value="editingContent.type" :options="contentTypeOptions" style="width: 100%;" />
      <h3>内容描述</h3>
      <a-textarea
        v-model:value="editingContent.description"
        placeholder="内容描述"
        :auto-size="{ minRows: 3, maxRows: 6 }"
      />
      <h3>内容数据</h3>
      <a-textarea
        v-model:value="editingContent.data"
        placeholder="请输入内容数据（文本、链接、JSON等）"
        :auto-size="{ minRows: 5, maxRows: 10 }"
      />
      <template #footer>
        <a-button key="back" @click="cancelEditContent">取消</a-button>
        <a-button key="submit" type="primary" :loading="state.updating" @click="updateContent">更新</a-button>
      </template>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router';
import { message } from 'ant-design-vue'
import { FileText, Link, StickyNote, MessageCircle, BookOpen } from 'lucide-vue-next';
import { knowledgeManagementApi } from '@/apis/admin_api';
import HeaderComponent from '@/components/HeaderComponent.vue';

const route = useRoute()
const router = useRouter()
const knowledgeInfo = ref(null)
const knowledgeContents = ref([])

const state = reactive({
  loading: false,
  adding: false,
  updating: false,
  openAddContentModal: false,
  openEditContentModal: false,
})

const contentTypeOptions = computed(() => {
  return [
    { label: '文本内容', value: 'text' },
    { label: '链接内容', value: 'link' },
    { label: '笔记内容', value: 'note' },
    { label: 'FAQ内容', value: 'faq' },
    { label: 'JSON数据', value: 'json' },
  ]
})

const emptyContentInfo = {
  title: '',
  description: '',
  type: 'text',
  data: '',
}

const newContent = reactive({
  ...emptyContentInfo,
})

const editingContent = reactive({
  ...emptyContentInfo,
})

const getContentIcon = (type) => {
  const iconMap = {
    text: FileText,
    link: Link,
    note: StickyNote,
    faq: MessageCircle,
    json: BookOpen,
  }
  return iconMap[type] || BookOpen
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString('zh-CN')
}

const loadKnowledgeInfo = () => {
  state.loading = true
  const knowledgeId = route.params.knowledge_id
  
  knowledgeManagementApi.getKnowledgeInfo(knowledgeId)
    .then(data => {
      console.log(data)
      knowledgeInfo.value = data.knowledge_info
      knowledgeContents.value = data.contents || []
      state.loading = false
    })
    .catch(error => {
      console.error('加载知识项详情失败:', error);
      message.error(error.message || '加载失败')
      state.loading = false
    })
}

const resetNewContent = () => {
  Object.assign(newContent, { ...emptyContentInfo })
}

const cancelAddContent = () => {
  state.openAddContentModal = false
  resetNewContent()
}

const addContent = () => {
  if (!newContent.title?.trim()) {
    message.error('内容标题不能为空')
    return
  }

  if (!newContent.data?.trim()) {
    message.error('内容数据不能为空')
    return
  }

  state.adding = true
  const knowledgeId = route.params.knowledge_id

  const requestData = {
    knowledge_id: knowledgeId,
    title: newContent.title.trim(),
    description: newContent.description?.trim() || '',
    type: newContent.type || 'text',
    data: newContent.data.trim(),
  }

  knowledgeManagementApi.addContent(requestData)
    .then(data => {
      console.log('添加成功:', data)
      loadKnowledgeInfo()
      resetNewContent()
      message.success('添加成功')
    })
    .catch(error => {
      console.error('添加内容失败:', error)
      message.error(error.message || '添加失败')
    })
    .finally(() => {
      state.adding = false
      state.openAddContentModal = false
    })
}

const editContent = (content) => {
  Object.assign(editingContent, {
    id: content.id,
    title: content.title,
    description: content.description || '',
    type: content.type,
    data: content.data,
  })
  state.openEditContentModal = true
}

const cancelEditContent = () => {
  state.openEditContentModal = false
  Object.assign(editingContent, { ...emptyContentInfo })
}

const updateContent = () => {
  if (!editingContent.title?.trim()) {
    message.error('内容标题不能为空')
    return
  }

  if (!editingContent.data?.trim()) {
    message.error('内容数据不能为空')
    return
  }

  state.updating = true

  const requestData = {
    content_id: editingContent.id,
    title: editingContent.title.trim(),
    description: editingContent.description?.trim() || '',
    type: editingContent.type || 'text',
    data: editingContent.data.trim(),
  }

  knowledgeManagementApi.updateContent(requestData)
    .then(data => {
      console.log('更新成功:', data)
      loadKnowledgeInfo()
      cancelEditContent()
      message.success('更新成功')
    })
    .catch(error => {
      console.error('更新内容失败:', error)
      message.error(error.message || '更新失败')
    })
    .finally(() => {
      state.updating = false
      state.openEditContentModal = false
    })
}

const deleteContent = (contentId) => {
  const knowledgeId = route.params.knowledge_id
  
  knowledgeManagementApi.deleteContent(knowledgeId, contentId)
    .then(data => {
      console.log('删除成功:', data)
      loadKnowledgeInfo()
      message.success('删除成功')
    })
    .catch(error => {
      console.error('删除内容失败:', error)
      message.error(error.message || '删除失败')
    })
}

const viewContent = (content) => {
  // 可以在这里实现查看内容的详细功能
  console.log('查看内容:', content)
}

const goBack = () => {
  router.push('/knowledge')
}

onMounted(() => {
  loadKnowledgeInfo()
})

</script>

<style lang="less" scoped>
.knowledge-info-container {
  padding: 0;
}

.knowledge-info {
  padding: 20px;

  .info-section {
    margin-bottom: 30px;
    padding: 20px;
    background-color: white;
    border-radius: 12px;
    box-shadow: 0px 1px 2px 0px rgba(16,24,40,.06),0px 1px 3px 0px rgba(16,24,40,.1);

    h2 {
      margin: 0 0 10px 0;
      font-size: 24px;
      font-weight: 600;
      color: var(--gray-900);
    }

    .description {
      margin: 0 0 15px 0;
      color: var(--gray-700);
      font-size: 14px;
      line-height: 1.5;
    }

    .tags {
      display: flex;
      gap: 8px;
    }
  }

  .content-section {
    h3 {
      margin: 0 0 20px 0;
      font-size: 18px;
      font-weight: 600;
      color: var(--gray-900);
    }

    .content-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .content-item {
      display: flex;
      align-items: center;
      padding: 16px;
      background-color: white;
      border-radius: 8px;
      box-shadow: 0px 1px 2px 0px rgba(16,24,40,.06),0px 1px 3px 0px rgba(16,24,40,.1);
      transition: box-shadow 0.2s ease-in-out;
      cursor: pointer;

      &:hover {
        box-shadow: 0px 4px 6px -2px rgba(16,24,40,.03),0px 12px 16px -4px rgba(16,24,40,.08);
      }

      .content-icon {
        width: 40px;
        height: 40px;
        margin-right: 12px;
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: #F5F8FF;
        border-radius: 6px;
        color: var(--main-color);
      }

      .content-info {
        flex: 1;

        h4 {
          margin: 0 0 4px 0;
          font-size: 16px;
          font-weight: 600;
          color: var(--gray-900);
        }

        p {
          margin: 0 0 8px 0;
          color: var(--gray-700);
          font-size: 14px;
          line-height: 1.4;
        }

        .content-meta {
          display: flex;
          gap: 12px;
          font-size: 12px;
          color: var(--gray-500);

          span {
            background-color: var(--gray-100);
            padding: 2px 6px;
            border-radius: 4px;
          }
        }
      }

      .content-actions {
        display: flex;
        gap: 8px;
      }
    }
  }
}

.add-content-modal, .edit-content-modal {
  h3 {
    margin-top: 10px;
  }
}
</style> 