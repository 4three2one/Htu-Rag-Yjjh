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
          
<!--          <div class="new-knowledge knowledge-card" @click="state.openNewKnowledgeModel=true">
            <div class="top">
              <div class="icon"><BookPlus /></div>
              <div class="info">
                <h3>新建知识项</h3>
              </div>
            </div>
            <p>创建和管理您的知识内容，包括文档、链接、笔记等，以增强 LLM 的上下文理解能力。</p>
          </div>-->
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
              <!-- <span class="meta-embed">
                <a-tag color="blue" v-if="knowledge.embed_info && knowledge.embed_info.name">{{ knowledge.embed_info.name }}</a-tag>
              </span> -->
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧层级预览区域 (2/10) -->
      <div class="knowledge-right">
        <div class="hierarchy-preview">
          <h3 class="hierarchy-title">结构预览</h3>
          <div class="hierarchy-tip">
            <small>💡 点击知识库名称可直接跳转到详情页</small>
          </div>
          <div class="hierarchy-content">
            <div v-if="state.loading" class="hierarchy-loading">
              <p>加载层级结构中...</p>
            </div>
            <a-tree
              v-else-if="hierarchyTreeData.length > 0"
              :tree-data="hierarchyTreeData"
              :default-expand-all="true"
              :show-line="true"
              :show-icon="true"
              class="hierarchy-tree"
              @select="handleTreeSelect"
            >
              <template #title="{ title, key }">
                <span class="tree-node-title clickable">{{ title }}</span>
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

const loadKnowledgeItems = async () => {
  state.loading = true
  try {
    const data = await knowledgeManagementApi.getKnowledge()
    console.log('API返回数据:', data)
    console.log('knowledge_items:', data.knowledge_items)
    
    // 获取层级数据用于排序
    let hierarchyData = []
    try {
      const hierarchyResponse = await knowledgeHierarchyApi.getAllKnowledgeHierarchy()
      hierarchyData = hierarchyResponse.all_hierarchy || []
    } catch (error) {
      console.warn('获取层级数据失败，将使用默认排序:', error)
    }
    
    // 过滤掉名称为"test"的项
    const filtered = (data.knowledge_items || []).filter(item => item.name !== 'test')
    
    // 根据层级数据中的 order 字段排序
    if (hierarchyData.length > 0) {
      // 创建层级数据映射
      const hierarchyMap = new Map()
      hierarchyData.forEach(hierarchy => {
        hierarchyMap.set(hierarchy.db_id, hierarchy)
      })
      
      // 按 order 字段排序，order 值越小越靠前
      filtered.sort((a, b) => {
        const aOrder = hierarchyMap.get(a.db_id)?.order || 999
        const bOrder = hierarchyMap.get(b.db_id)?.order || 999
        return aOrder - bOrder
      })
    } else {
      // 如果没有层级数据，将包含"其他"的项排到最后
      const others = filtered.filter(item => item.name.includes('其他'))
      const normal = filtered.filter(item => !item.name.includes('其他'))
      filtered.splice(0, filtered.length, ...normal, ...others)
    }
    
    knowledgeItems.value = filtered
    console.log('设置后的knowledgeItems:', knowledgeItems.value)
    
    // 加载层级结构
    await loadHierarchyStructure()
  } catch (error) {
    console.error('加载知识项列表失败:', error);
    if (error.message.includes('权限')) {
      message.error('需要管理员权限访问知识管理')
    }
  } finally {
    state.loading = false
  }
}

// 加载层级结构
const loadHierarchyStructure = async () => {
  try {
    const hierarchyData = await knowledgeHierarchyApi.getAllKnowledgeHierarchy()
    console.log('层级数据:', hierarchyData)
    console.log('知识项数据:', knowledgeItems.value)
    
    if (hierarchyData.all_hierarchy && hierarchyData.all_hierarchy.length > 0) {
      // 构建树形结构
      const treeData = buildHierarchyTree(hierarchyData.all_hierarchy, knowledgeItems.value)
      console.log('构建的树形数据:', treeData)
      hierarchyTreeData.value = treeData
    } else {
      // 如果没有层级数据，将所有知识项作为根节点显示
      const flatTreeData = knowledgeItems.value.map(item => ({
        key: item.db_id,
        title: item.name,
        children: []
      }))
      console.log('平铺的树形数据:', flatTreeData)
      hierarchyTreeData.value = flatTreeData
    }
  } catch (error) {
    console.error('加载层级结构失败:', error)
    // 出错时也显示所有知识项作为根节点
    const fallbackTreeData = knowledgeItems.value.map(item => ({
      key: item.db_id,
      title: item.name,
      children: []
    }))
    console.log('回退的树形数据:', fallbackTreeData)
    hierarchyTreeData.value = fallbackTreeData
  }
}

// 构建层级树形结构
const buildHierarchyTree = (hierarchyList, knowledgeItems) => {
  console.log('开始构建层级树，层级列表:', hierarchyList)
  console.log('知识项列表:', knowledgeItems)
  
  // 创建知识项映射
  const knowledgeMap = new Map()
  knowledgeItems.forEach(item => {
    knowledgeMap.set(item.db_id, item)
  })

  // 创建层级关系映射
  const parentChildMap = new Map()
  const childParentMap = new Map()
  
  hierarchyList.forEach(hierarchy => {
    if (hierarchy.parent_db_id) {
      // 建立父子关系映射
      if (!parentChildMap.has(hierarchy.parent_db_id)) {
        parentChildMap.set(hierarchy.parent_db_id, [])
      }
      parentChildMap.get(hierarchy.parent_db_id).push(hierarchy.db_id)
      
      // 建立子父关系映射
      childParentMap.set(hierarchy.db_id, hierarchy.parent_db_id)
    }
  })

  console.log('父子关系映射:', Object.fromEntries(parentChildMap))
  console.log('子父关系映射:', Object.fromEntries(childParentMap))

  // 构建树形结构
  const treeData = []
  const processed = new Set()

  // 1. 先处理根节点（没有父级的节点）
  knowledgeItems.forEach(item => {
    if (!childParentMap.has(item.db_id) && !processed.has(item.db_id)) {
      console.log('处理根节点:', item.name, item.db_id)
      const node = {
        key: item.db_id,
        title: item.name,
        children: buildChildrenNodes(item.db_id, parentChildMap, knowledgeMap, processed)
      }
      treeData.push(node)
      processed.add(item.db_id)
    }
  })

  // 2. 处理有层级关系但父级不存在的节点（作为根节点显示）
  hierarchyList.forEach(hierarchy => {
    if (hierarchy.parent_db_id && !knowledgeMap.has(hierarchy.parent_db_id) && !processed.has(hierarchy.db_id)) {
      const knowledge = knowledgeMap.get(hierarchy.db_id)
      if (knowledge) {
        console.log('处理孤立节点:', knowledge.name, hierarchy.db_id)
        const node = {
          key: hierarchy.db_id,
          title: knowledge.name,
          children: buildChildrenNodes(hierarchy.db_id, parentChildMap, knowledgeMap, processed)
        }
        treeData.push(node)
        processed.add(hierarchy.db_id)
      }
    }
  })

  console.log('最终树形数据:', treeData)
  return treeData
}

// 递归构建子节点
const buildChildrenNodes = (parentId, parentChildMap, knowledgeMap, processed) => {
  const children = []
  const childIds = parentChildMap.get(parentId) || []
  
  console.log(`构建 ${parentId} 的子节点:`, childIds)
  
  childIds.forEach(childId => {
    if (!processed.has(childId)) {
      const knowledge = knowledgeMap.get(childId)
      if (knowledge) {
        console.log(`添加子节点: ${knowledge.name} (${childId}) 到父节点 ${parentId}`)
        const node = {
          key: childId,
          title: knowledge.name,
          children: buildChildrenNodes(childId, parentChildMap, knowledgeMap, processed)
        }
        children.push(node)
        processed.add(childId)
      } else {
        console.warn(`未找到知识项: ${childId}`)
      }
    } else {
      console.log(`跳过已处理的子节点: ${childId}`)
    }
  })

  console.log(`父节点 ${parentId} 的子节点数量:`, children.length)
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
    parent_db_id: newKnowledge.parent_db_id || null, // 确保undefined转换为null
  }
  try {
    const data = await knowledgeManagementApi.createKnowledge(requestData)
    // 后端已经在创建时处理了层级关系，无需重复添加
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

// 处理树节点点击事件
const handleTreeSelect = (selectedKeys, info) => {
  if (selectedKeys.length > 0) {
    const selectedKey = selectedKeys[0]
    console.log('点击的树节点:', selectedKey)
    
    // 检查是否是有效的知识库ID
    const knowledgeItem = knowledgeItems.value.find(item => item.db_id === selectedKey)
    if (knowledgeItem) {
      console.log('跳转到知识库:', knowledgeItem.name)
      navigateToKnowledge(selectedKey)
    } else {
      console.warn('未找到对应的知识库:', selectedKey)
    }
  }
}

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
  flex: 4;
  overflow-y: auto;
}

.knowledge-right {
  flex: 6;
  min-width: 500px;
  max-width: 600px;
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
  padding: 16px 20px 8px 20px;
  margin: 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.hierarchy-tip {
  padding: 8px 20px;
  background-color: #f6ffed;
  border-bottom: 1px solid #f0f0f0;
  
  small {
    color: #52c41a;
    font-size: 12px;
  }
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
    
    &.clickable {
      cursor: pointer;
      transition: all 0.2s ease;
      padding: 2px 4px;
      border-radius: 4px;
      
      &:hover {
        color: #1890ff;
        background-color: #f0f8ff;
        text-decoration: none;
      }
      
      &:active {
        background-color: #e6f7ff;
      }
    }
  }
  
  // 为树节点添加更好的视觉反馈
  :deep(.ant-tree-node-content-wrapper) {
    &:hover {
      background-color: transparent;
    }
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

.hierarchy-loading {
  text-align: center;
  color: #666;
  padding: 40px 20px;
  
  p {
    margin: 0;
    font-size: 14px;
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