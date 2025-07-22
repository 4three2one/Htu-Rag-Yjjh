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
      <h3>父级知识库</h3>
      <a-select v-model:value="newKnowledge.parent_db_id" :options="parentOptions" allow-clear placeholder="可不选，表示根节点" style="width: 100%;" />
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
      <template v-if="hierarchyTree.length">
        <KnowledgeTree :tree="hierarchyTree" @select="navigateToKnowledge" />
      </template>
      <template v-else>
        <div
          v-for="knowledge in knowledgeItems"
          :key="knowledge.id"
          class="knowledge knowledge-card"
          @click="navigateToKnowledge(knowledge.id)">
          <div class="top">
            <div class="icon"><ReadFilled /></div>
            <div class="info">
              <h3>{{ knowledge.name }}</h3>
              <div class="meta-row-time">
                <span class="meta-right" v-if="knowledge.created_at">
                  {{ formatCreateTime(knowledge.created_at) }}
                </span>
              </div>
            </div>
          </div>
          <div class="meta-bottom">
            <span class="meta-left">
              {{ (knowledge.content_count ?? 0) + ' 文档' }}
            </span>
            <span class="meta-embed">
              <a-tag color="blue" v-if="knowledge.embed_info && knowledge.embed_info.name">{{ knowledge.embed_info.name }}</a-tag>
            </span>
          </div>
        </div>
      </template>
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
import { knowledgeHierarchyApi } from '@/apis/admin_api';
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

const hierarchyTree = ref([])
const allHierarchy = ref([])
const dbIdToName = ref({})

// 构建树结构
function buildHierarchyTree(hierarchyList, dbIdToNameMap) {
  const idMap = {}
  const tree = []
  hierarchyList.forEach(item => {
    idMap[item.db_id] = { ...item, children: [] }
  })
  hierarchyList.forEach(item => {
    if (item.parent_db_id && idMap[item.parent_db_id]) {
      idMap[item.parent_db_id].children.push(idMap[item.db_id])
    } else {
      tree.push(idMap[item.db_id])
    }
  })
  // 补充名称
  function fillName(node) {
    node.name = dbIdToNameMap[node.db_id] || node.db_id
    node.children.forEach(fillName)
  }
  tree.forEach(fillName)
  return tree
}

const loadHierarchy = async () => {
  // 获取所有层级
  const res = await knowledgeHierarchyApi.getAllKnowledgeHierarchy()
  allHierarchy.value = res.all_hierarchy || []
  // 获取所有知识库名称
  const dbListRes = await knowledgeManagementApi.getKnowledge()
  const dbList = dbListRes.knowledge_items || []
  dbIdToName.value = {}
  dbList.forEach(db => { dbIdToName.value[db.db_id] = db.name })
  hierarchyTree.value = buildHierarchyTree(allHierarchy.value, dbIdToName.value)
}

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

// 新建知识库表单增加parent_db_id
const newKnowledge = reactive({
  ...emptyKnowledgeInfo,
  parent_db_id: null,
})

const loadKnowledgeItems = () => {
  state.loading = true
  knowledgeManagementApi.getKnowledge()
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

// createKnowledge时传递parent_db_id到层级表
const createKnowledge = async () => {
  if (!newKnowledge.name?.trim()) {
    message.error('知识项名称不能为空')
    return
  }
  state.creating = true
  const requestData = {
    knowledge_name: newKnowledge.name.trim(),
    description: newKnowledge.description?.trim() || '',
    type: newKnowledge.type || 'document',
    parent_db_id: newKnowledge.parent_db_id || null, // 新增父级知识库字段
  }
  try {
    const data = await knowledgeManagementApi.createKnowledge(requestData)
    // 创建成功后，写入层级关系
    if (data && data.db_id) {
      await knowledgeHierarchyApi.addKnowledgeHierarchy({ db_id: data.db_id, parent_db_id: newKnowledge.parent_db_id })
    }
    loadKnowledgeItems()
    loadHierarchy()
    resetNewKnowledge()
    message.success('创建成功')
  } catch (error) {
    console.error('创建知识项失败:', error)
    message.error(error.message || '创建失败')
  } finally {
    state.creating = false
    state.openNewKnowledgeModel = false
  }
}

const navigateToKnowledge = (knowledgeId) => {
  router.push({ path: `/knowledge/${knowledgeId}` });
};

function formatCreateTime(val) {
  if (!val) return '-';
  // 支持时间戳（秒/毫秒）或 ISO 字符串
  if (typeof val === 'number' || /^\d+$/.test(val)) {
    const ts = String(val).length === 10 ? val * 1000 : Number(val);
    return new Date(ts).toLocaleString();
  }
  return new Date(val).toLocaleString();
}

watch(() => route.path, (newPath, oldPath) => {
  if (newPath === '/knowledge') {
    loadKnowledgeItems();
  }
});

onMounted(() => {
  loadKnowledgeItems()
  loadHierarchy()
})

// 新建知识库时选择父级
const parentOptions = computed(() => {
  // 只允许选择当前 knowledgeItems 作为父级
  return knowledgeItems.value.map(db => ({
    label: db.name,
    value: db.db_id
  }))
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
.knowledge-card .info h3 {
  font-weight: bold;
  font-size: 18px;
  margin-bottom: 0;
}
.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #888;
  font-size: 13px;
  margin-top: 4px;
}
.meta-left {
  font-weight: 500;
}
.meta-embed {
  margin-left: 8px;
}
.meta-row-time {
  margin-top: 2px;
  color: #aaa;
  font-size: 12px;
  text-align: right;
}
.meta-right {
  font-style: italic;
}
.meta-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #888;
  font-size: 13px;
  margin-top: 10px;
  padding: 0 8px 4px 8px;
}
.meta-left {
  font-weight: 500;
}
.meta-embed {
  margin-left: 8px;
}
</style> 

<script>
// 简单递归组件用于树状展示
import { defineComponent, h } from 'vue'
export const KnowledgeTree = defineComponent({
  name: 'KnowledgeTree',
  props: { tree: { type: Array, required: true } },
  emits: ['select'],
  setup(props, { emit }) {
    const renderTree = (nodes, level = 0) => nodes.map(node =>
      h('div', { style: { marginLeft: `${level * 24}px`, cursor: 'pointer', fontWeight: level === 0 ? 'bold' : 'normal' }, onClick: () => emit('select', node.db_id) }, [
        node.name,
        node.children && node.children.length ? renderTree(node.children, level + 1) : null
      ])
    )
    return () => h('div', {}, renderTree(props.tree))
  }
})
</script> 