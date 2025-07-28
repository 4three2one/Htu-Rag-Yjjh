<template>
  <div class="reference-display" v-if="referenceData">
    <div class="reference-header" @click="toggleCollapse">
      <div class="header-left">
        <h4>📚 引用来源</h4>
<!--        <span class="reference-count">共 {{ referenceData.total }} 个片段</span> <span class="reference-count">共 {{ referenceData.total }} 个片段</span>-->
      </div>
      <div class="header-right">
        <span class="collapse-icon" :class="{ 'collapsed': isCollapsed }">
          ▼
        </span>
      </div>
    </div>
    
    <div class="reference-list" v-show="!isCollapsed">
      <div 
        v-for="(chunk, index) in referenceData.chunks" 
        :key="chunk.id" 
        class="reference-item"
        :class="{ 'is-image': chunk.doc_type === 'image' }"
      >
        <div class="reference-header">
          <div class="document-info">
            <span class="document-name">{{ chunk.document_name }}</span>
<!--            <span class="chunk-id">#{{ chunk.id }}</span>-->
          </div>
<!--          <div class="similarity-info">
            <span class="similarity-score">
              相似度: {{ formatSimilarity(chunk.similarity) }}%
            </span>
          </div>-->
        </div>
        
        <div class="reference-content">
          <div class="content-text" v-if="chunk.content">
            {{ chunk.content }}
          </div>
<!--          <div class="content-image" v-if="chunk.doc_type === 'image'">
            <img 
              v-if="chunk.image_id" 
              :src="getImageUrl(chunk.image_id)" 
              :alt="chunk.document_name"
              class="reference-image"
            />
            <div v-else class="image-placeholder">
              📷 图片内容
            </div>
          </div>-->
        </div>
        
<!--        <div class="reference-footer">
          <span class="doc-type" v-if="chunk.doc_type">
            {{ getDocTypeLabel(chunk.doc_type) }}
          </span>
          <span class="vector-similarity" v-if="chunk.vector_similarity">
            向量相似度: {{ formatSimilarity(chunk.vector_similarity) }}%
          </span>
        </div>-->
      </div>
    </div>
    
<!--    <div class="reference-summary" v-if="referenceData.doc_aggs && referenceData.doc_aggs.length > 0" v-show="!isCollapsed">
      <h5>📊 文档统计</h5>
      <div class="doc-aggs">
        <div
          v-for="agg in referenceData.doc_aggs"
          :key="agg.doc_id"
          class="doc-agg-item"
        >
          <span class="doc-name">{{ agg.doc_name }}</span>
          <span class="doc-count">{{ agg.count }} 个片段</span>
        </div>
      </div>
    </div>-->
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  reference: {
    type: [String, Object],
    default: null
  }
})

// 折叠状态
const isCollapsed = ref(false)

// 切换折叠状态
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

// 解析引用数据
const referenceData = computed(() => {
  if (!props.reference) return null
  
  // 处理空对象的情况
  if (props.reference === null || props.reference === undefined) return null
  
  try {
    let parsedData
    // 如果是字符串，尝试解析JSON
    if (typeof props.reference === 'string') {
      parsedData = JSON.parse(props.reference)
    } else {
      // 如果已经是对象，直接使用
      parsedData = props.reference
    }
    
    // 检查解析后的数据是否为空或无效
    if (!parsedData || typeof parsedData !== 'object') return null
    
    // 检查是否为空对象 {}
    if (Object.keys(parsedData).length === 0) return null
    
    // 检查是否有有效的chunks数据
    if (!parsedData.chunks || !Array.isArray(parsedData.chunks) || parsedData.chunks.length === 0) {
      return null
    }
    
    return parsedData
  } catch (error) {
    console.error('解析引用数据失败:', error)
    return null
  }
})

// 格式化相似度
const formatSimilarity = (similarity) => {
  if (typeof similarity === 'number') {
    return (similarity * 100).toFixed(1)
  }
  return '0.0'
}

// 获取文档类型标签
const getDocTypeLabel = (docType) => {
  const typeMap = {
    'image': '图片',
    'pdf': 'PDF',
    'docx': 'Word文档',
    'txt': '文本文件',
    '': '文档'
  }
  return typeMap[docType] || '文档'
}

// 获取图片URL（这里需要根据你的实际API调整）
const getImageUrl = (imageId) => {
  // 这里需要根据你的实际API来构建图片URL
  // 例如: `/api/images/${imageId}`
  return `/api/images/${imageId}`
}
</script>

<style lang="less" scoped>
.reference-display {
  margin-top: 16px;
  padding: 16px;
  background-color: var(--gray-50);
  border-radius: 12px;
  border: 1px solid var(--gray-200);
  
  .reference-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    cursor: pointer;
    padding: 8px;
    border-radius: 8px;
    transition: background-color 0.2s ease;
    
    &:hover {
      background-color: var(--gray-100);
    }
    
    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
      
      h4 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: var(--gray-800);
      }
      
      .reference-count {
        font-size: 13px;
        color: var(--gray-600);
        background-color: var(--gray-100);
        padding: 4px 8px;
        border-radius: 12px;
      }
    }
    
    .header-right {
      .collapse-icon {
        font-size: 12px;
        color: var(--gray-600);
        transition: transform 0.2s ease;
        
        &.collapsed {
          transform: rotate(-90deg);
        }
      }
    }
  }
  
  .reference-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  .reference-item {
    background-color: white;
    border: 1px solid var(--gray-200);
    border-radius: 8px;
    padding: 12px;
    transition: all 0.2s ease;
    
    &:hover {
      border-color: var(--main-300);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    
    &.is-image {
      border-left: 4px solid var(--main-500);
    }
    
    .reference-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      
      .document-info {
        display: flex;
        align-items: center;
        gap: 8px;
        
        .document-name {
          font-weight: 600;
          color: var(--gray-800);
          font-size: 14px;
        }
        
        .chunk-id {
          font-size: 12px;
          color: var(--gray-500);
          background-color: var(--gray-100);
          padding: 2px 6px;
          border-radius: 4px;
        }
      }
      
      .similarity-info {
        .similarity-score {
          font-size: 12px;
          color: var(--main-600);
          font-weight: 500;
        }
      }
    }
    
    .reference-content {
      margin-bottom: 8px;
      
      .content-text {
        font-size: 13px;
        line-height: 1.5;
        color: var(--gray-700);
        background-color: var(--gray-100);
        padding: 8px;
        border-radius: 4px;
        white-space: pre-wrap;
        word-break: break-word;
        max-height: 120px;
        overflow-y: auto;
      }
      
      .content-image {
        .reference-image {
          max-width: 100%;
          max-height: 200px;
          border-radius: 4px;
          border: 1px solid var(--gray-200);
        }
        
        .image-placeholder {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100px;
          background-color: var(--gray-100);
          border: 2px dashed var(--gray-300);
          border-radius: 4px;
          color: var(--gray-500);
          font-size: 14px;
        }
      }
    }
    
    .reference-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      
      .doc-type {
        color: var(--gray-600);
        background-color: var(--gray-100);
        padding: 2px 6px;
        border-radius: 4px;
      }
      
      .vector-similarity {
        color: var(--gray-500);
      }
    }
  }
  
  .reference-summary {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid var(--gray-200);
    
    h5 {
      margin: 0 0 12px 0;
      font-size: 14px;
      font-weight: 600;
      color: var(--gray-800);
    }
    
    .doc-aggs {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    
    .doc-agg-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      background-color: var(--gray-100);
      border-radius: 6px;
      
      .doc-name {
        font-size: 13px;
        color: var(--gray-700);
        font-weight: 500;
      }
      
      .doc-count {
        font-size: 12px;
        color: var(--gray-600);
        background-color: white;
        padding: 2px 6px;
        border-radius: 4px;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .reference-display {
    padding: 12px;
    
    .reference-header {
      .header-left {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
      }
    }
    
    .reference-item {
      .reference-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;
      }
      
      .reference-footer {
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;
      }
    }
  }
}
</style> 