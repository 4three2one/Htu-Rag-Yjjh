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

    <!-- 左右分栏布局 -->
    <div class="knowledge-layout">
      <!-- 左侧内容区域 (8/10) -->
      <div class="knowledge-left">
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
        </div>
      </div>

      <!-- 右侧层级预览区域 (2/10) -->
      <div class="knowledge-right">
        <div class="hierarchy-preview">
          <h3 class="hierarchy-title">层级结构预览</h3>
          <div class="hierarchy-content">
            <a-tree
              v-if="hierarchyTreeData.length > 0"
              :tree-data="hierarchyTreeData"
              :default-expand-all="true"
              :show-line="true"
              :show-icon="true"
              class="hierarchy-tree"
            >
              <template #title="{ title, key }">
                <span class="tree-node-title">{{ title }}</span>
              </template>
            </a-tree>
            <div v-else class="hierarchy-empty">
              <p>暂无层级结构</p>
              <p class="hierarchy-tip">创建知识项时可选择父级来构建层级关系</p>
            </div>
          </div>
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

// 知识类型选项
const knowledgeTypeOptions = [
  { label: '文档', value: 'document' },
  { label: '链接', value: 'url' },
  { label: '笔记', value: 'note' },
]

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

// 层级树数据
const hierarchyTreeData = ref([])

const loadKnowledgeItems = () => {
  state.loading = true
  knowledgeManagementApi.getKnowledge()
    .then(data => {
      console.log('API返回数据:', data)
      console.log('knowledge_items:', data.knowledge_items)
      knowledgeItems.value = data.knowledge_items || []
      console.log('设置后的knowledgeItems:', knowledgeItems.value)
      state.loading = false
      // 加载层级结构
      loadHierarchyStructure()
    })
    .catch(error => {
      console.error('加载知识项列表失败:', error);
      if (error.message.includes('权限')) {
        message.error('需要管理员权限访问知识管理')
      }
      state.loading = false
    })
}

// 加载层级结构
const loadHierarchyStructure = async () => {
  try {
    const hierarchyData = await knowledgeHierarchyApi.getAllKnowledgeHierarchy()
    console.log('层级数据:', hierarchyData)
    
    if (hierarchyData.all_hierarchy && hierarchyData.all_hierarchy.length > 0) {
      // 构建树形结构
      const treeData = buildHierarchyTree(hierarchyData.all_hierarchy, knowledgeItems.value)
      hierarchyTreeData.value = treeData
    } else {
      hierarchyTreeData.value = []
    }
  } catch (error) {
    console.error('加载层级结构失败:', error)
    hierarchyTreeData.value = []
  }
}

// 构建层级树形结构
const buildHierarchyTree = (hierarchyList, knowledgeItems) => {
  // 创建知识项映射
  const knowledgeMap = new Map()
  knowledgeItems.forEach(item => {
    knowledgeMap.set(item.db_id, item)
  })

  // 创建层级映射
  const hierarchyMap = new Map()
  hierarchyList.forEach(h => {
    hierarchyMap.set(h.db_id, h)
  })

  // 构建树形结构
  const treeData = []
  const processed = new Set()

  // 先处理根节点（没有父级的节点）
  hierarchyList.forEach(hierarchy => {
    if (!hierarchy.parent_db_id && !processed.has(hierarchy.db_id)) {
      const knowledge = knowledgeMap.get(hierarchy.db_id)
      if (knowledge) {
        const node = {
          key: hierarchy.db_id,
          title: knowledge.name,
          children: getChildren(hierarchy.db_id, hierarchyList, knowledgeMap, processed)
        }
        treeData.push(node)
        processed.add(hierarchy.db_id)
      }
    }
  })

  // 处理没有层级关系的知识项（作为根节点）
  knowledgeItems.forEach(item => {
    if (!processed.has(item.db_id)) {
      const node = {
        key: item.db_id,
        title: item.name,
        children: []
      }
      treeData.push(node)
      processed.add(item.db_id)
    }
  })

  return treeData
}

// 递归获取子节点
const getChildren = (parentId, hierarchyList, knowledgeMap, processed) => {
  const children = []
  
  hierarchyList.forEach(hierarchy => {
    if (hierarchy.parent_db_id === parentId && !processed.has(hierarchy.db_id)) {
      const knowledge = knowledgeMap.get(hierarchy.db_id)
      if (knowledge) {
        const node = {
          key: hierarchy.db_id,
          title: knowledge.name,
          children: getChildren(hierarchy.db_id, hierarchyList, knowledgeMap, processed)
        }
        children.push(node)
        processed.add(hierarchy.db_id)
      }
    }
  })

  return children
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

// 左右分栏布局
.knowledge-layout {
  display: flex;
  gap: 20px;
  height: calc(100vh - 120px);
  padding: 20px;
}

.knowledge-left {
  flex: 8;
  overflow-y: auto;
}

.knowledge-right {
  flex: 2;
  min-width: 250px;
  max-width: 300px;
}

// 层级预览样式
.hierarchy-preview {
  background: white;
  border-radius: 12px;
  box-shadow: 0px 1px 2px 0px rgba(16,24,40,.06),0px 1px 3px 0px rgba(16,24,40,.1);
  border: 2px solid white;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.hierarchy-title {
  padding: 16px 20px;
  margin: 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.hierarchy-content {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.hierarchy-tree {
  .tree-node-title {
    font-size: 14px;
    color: #333;
  }
}

.hierarchy-empty {
  text-align: center;
  color: #999;
  padding: 40px 20px;
  
  p {
    margin: 8px 0;
    font-size: 14px;
  }
  
  .hierarchy-tip {
    font-size: 12px;
    color: #ccc;
  }
}

.knowledge-items {
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

// 响应式设计
@media (max-width: 1200px) {
  .knowledge-layout {
    flex-direction: column;
  }
  
  .knowledge-right {
    min-width: auto;
    max-width: none;
    height: 300px;
  }
}
</style> 