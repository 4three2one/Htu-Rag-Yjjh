<template>
  <div class="knowledge-container layout-container">
    <HeaderComponent title="知识管理" :loading="state.loading">
      <template #actions>
        <a-button type="primary" @click="state.openNewKnowledgeModel=true">
          新建知识项
        </a-button>
      </template>
    </HeaderComponent>

    <a-modal :open="state.openNewKnowledgeModel" title="新建知识项" @ok="createKnowledge" @cancel="cancelCreateKnowledge" class="new-knowledge-modal">
      <h3>知识项名称<span style="color: var(--error-color)">*</span></h3>
      <a-input v-model:value="newKnowledge.name" placeholder="新建知识项名称" />
      <h3>知识类型</h3>
      <a-select v-model:value="newKnowledge.type" :options="knowledgeTypeOptions" style="width: 100%;" />
      <h3 style="margin-top: 20px;">知识描述</h3>
      <p style="color: var(--gray-700); font-size: 14px;">在智能体流程中，这里的描述会作为工具的描述。智能体会根据知识项的标题和描述来选择合适的工具。所以这里描述的越详细，智能体越容易选择到合适的工具。</p>
      <a-textarea
        v-model:value="newKnowledge.description"
        placeholder="新建知识项描述"
        :auto-size="{ minRows: 5, maxRows: 10 }"
      />
      <template #footer>
        <a-button key="back" @click="cancelCreateKnowledge">取消</a-button>
        <a-button key="submit" type="primary" :loading="state.creating" @click="createKnowledge">创建</a-button>
      </template>
    </a-modal>
    <div class="knowledge-items">
      <!-- 调试信息 -->
      <div v-if="knowledgeItems.length === 0" style="grid-column: 1 / -1; text-align: center; padding: 20px; color: #666;">
        正在加载知识项... (数量: {{ knowledgeItems.length }})
      </div>
      
      <div class="new-knowledge knowledge-card" @click="state.openNewKnowledgeModel=true">
        <div class="top">
          <div class="icon"><BookPlus /></div>
          <div class="info">
            <h3>新建知识项</h3>
          </div>
        </div>
        <p>创建和管理您的知识内容，包括文档、链接、笔记等，以增强 LLM 的上下文理解能力。</p>
      </div>
      <div
        v-for="knowledge in knowledgeItems"
        :key="knowledge.id"
        class="knowledge knowledge-card"
        @click="navigateToKnowledge(knowledge.id)">
        <div class="top">
          <div class="icon"><ReadFilled /></div>
          <div class="info">
            <h3>{{ knowledge.name }}</h3>
            <p><span>{{ knowledge.content_count || 0 }} 内容</span></p>
          </div>
        </div>
        <a-tooltip :title="knowledge.description || '暂无描述'">
          <p class="description">{{ knowledge.description || '暂无描述' }}</p>
        </a-tooltip>
        <div class="tags">
          <a-tag color="blue" v-if="knowledge.type">{{ knowledge.type }}</a-tag>
          <a-tag color="green" v-if="knowledge.status">{{ knowledge.status }}</a-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, watch, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router';
import { useConfigStore } from '@/stores/config';
import { message } from 'ant-design-vue'
import { ReadFilled } from '@ant-design/icons-vue'
import { BookPlus } from 'lucide-vue-next';
import { knowledgeManagementApi } from '@/apis/admin_api';
import HeaderComponent from '@/components/HeaderComponent.vue';

const route = useRoute()
const router = useRouter()
const knowledgeItems = ref([])
const configStore = useConfigStore()

const state = reactive({
  loading: false,
  creating: false,
  openNewKnowledgeModel: false,
})

const knowledgeTypeOptions = computed(() => {
  return [
    { label: '文档知识', value: 'document' },
    // { label: '链接知识', value: 'link' },
    // { label: '笔记知识', value: 'note' },
    // { label: 'FAQ知识', value: 'faq' },
    // { label: '其他', value: 'other' },
  ]
})

const emptyKnowledgeInfo = {
  name: '',
  description: '',
  type: 'document',
}

const newKnowledge = reactive({
  ...emptyKnowledgeInfo,
})

const loadKnowledgeItems = () => {
  state.loading = true
  knowledgeManagementApi.getKnowledgeItems()
    .then(data => {
      console.log('API返回数据:', data)
      console.log('knowledge_items:', data.knowledge_items)
      knowledgeItems.value = data.knowledge_items || []
      console.log('设置后的knowledgeItems:', knowledgeItems.value)
      state.loading = false
    })
    .catch(error => {
      console.error('加载知识项列表失败:', error);
      if (error.message.includes('权限')) {
        message.error('需要管理员权限访问知识管理')
      }
      state.loading = false
    })
}

const resetNewKnowledge = () => {
  Object.assign(newKnowledge, { ...emptyKnowledgeInfo })
}

const cancelCreateKnowledge = () => {
  state.openNewKnowledgeModel = false
}

const createKnowledge = () => {
  if (!newKnowledge.name?.trim()) {
    message.error('知识项名称不能为空')
    return
  }

  state.creating = true

  const requestData = {
    knowledge_name: newKnowledge.name.trim(),
    description: newKnowledge.description?.trim() || '',
    type: newKnowledge.type || 'document',
  }

  knowledgeManagementApi.createKnowledgeItem(requestData)
    .then(data => {
      console.log('创建成功:', data)
      loadKnowledgeItems()
      resetNewKnowledge()
      message.success('创建成功')
    })
    .catch(error => {
      console.error('创建知识项失败:', error)
      message.error(error.message || '创建失败')
    })
    .finally(() => {
      state.creating = false
      state.openNewKnowledgeModel = false
    })
}

const navigateToKnowledge = (knowledgeId) => {
  router.push({ path: `/knowledge/${knowledgeId}` });
};

watch(() => route.path, (newPath, oldPath) => {
  if (newPath === '/knowledge') {
    loadKnowledgeItems();
  }
});

onMounted(() => {
  loadKnowledgeItems()
})

</script>

<style lang="less" scoped>
.knowledge-actions, .content-actions {
  margin-bottom: 20px;
}
.knowledge-items {
  padding: 20px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;

  .new-knowledge {
    background-color: #F0F3F4;
  }
}

.knowledge {
  background-color: white;
  box-shadow: 0px 1px 2px 0px rgba(16,24,40,.06),0px 1px 3px 0px rgba(16,24,40,.1);
  border: 2px solid white;
  transition: box-shadow 0.2s ease-in-out;

  &:hover {
    box-shadow: 0px 4px 6px -2px rgba(16,24,40,.03),0px 12px 16px -4px rgba(16,24,40,.08);
  }
}

.knowledge-card, .knowledge {
  width: 100%;
  padding: 10px;
  border-radius: 12px;
  height: 160px;
  padding: 20px;
  cursor: pointer;

  .top {
    display: flex;
    align-items: center;
    height: 50px;
    margin-bottom: 10px;

    .icon {
      width: 50px;
      height: 50px;
      font-size: 28px;
      margin-right: 10px;
      display: flex;
      justify-content: center;
      align-items: center;
      background-color: #F5F8FF;
      border-radius: 8px;
      border: 1px solid #E0EAFF;
      color: var(--main-color);
    }

    .info {
      h3, p {
        margin: 0;
        color: black;
      }

      h3 {
        font-size: 16px;
        font-weight: bold;
      }

      p {
        color: var(--gray-900);
        font-size: small;
      }
    }
  }

  .description {
    color: var(--gray-900);
    overflow: hidden;
    display: -webkit-box;
    line-clamp: 1;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    text-overflow: ellipsis;
    margin-bottom: 10px;
  }
}

.knowledge-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  flex-direction: column;
  color: var(--gray-900);
}

.knowledge-container {
  padding: 0;
}

.new-knowledge-modal {
  h3 {
    margin-top: 10px;
  }
}
</style> 