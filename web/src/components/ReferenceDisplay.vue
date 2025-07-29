<template>
  <div class="reference-display" v-if="referenceData">
    <div class="reference-header" @click="toggleCollapse">
      <div class="header-left">
        <h4>📚 参考知识</h4>
        <span class="reference-count<!---->"></span>
      </div>
      <div class="header-right">
        <span class="collapse-icon" :class="{ 'collapsed': isCollapsed }">
          ▼
        </span>
      </div>
    </div>

<!--    <div class="reference-summary" v-if="referenceData.doc_aggs && referenceData.doc_aggs.length > 0"
         v-show="!isCollapsed">
      <div class="doc-aggs">
        <div
          v-for="agg in referenceData.doc_aggs"
          :key="agg.doc_id"
          class="doc-agg-item"
        >
          <span class="doc-name">{{ agg.doc_name }}</span>
&lt;!&ndash;          <span class="doc-count">{{ agg.count }} 个片段</span>&ndash;&gt;
        </div>
      </div>
    </div>-->

    <div class="reference-list" v-show="!isCollapsed">
      <div
          v-for="(chunk, index) in referenceData.chunks"
          :key="chunk.id"
          class="reference-item"
          :class="{ 'is-image': chunk.doc_type === 'image' }"
      >
        <div class="reference-header">
          <div class="document-info">
            <span class="document-name clickable" @click="openFilePreview(chunk)">{{ chunk.document_name }}</span>
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
            <div class="content-image" v-if="chunk.doc_type === 'image'">
              <img
                v-if="chunk.image_id"
                :src="getImageUrl(chunk.image_id)"
                class="reference-image"
                @click="openImageModal(chunk.image_id, chunk.document_name)"
                :alt="chunk.document_name"
              />
            </div>
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

  </div>

  <!-- 图片放大模态框 -->
  <div v-if="imageModalVisible" class="image-modal-overlay" @click="closeImageModal">
    <div class="image-modal-content" @click.stop>
      <div class="image-modal-header">
        <span class="image-modal-title">{{ currentImageTitle }}</span>
        <button class="image-modal-close" @click="closeImageModal">×</button>
      </div>
      <div class="image-modal-body" :class="{ 'loading': imageLoading }">
        <img 
          v-if="!imageError"
          :src="getImageUrl(currentImageId)" 
          :alt="currentImageTitle"
          class="image-modal-image"
          @load="onImageLoad"
          @error="onImageError"
        />
        <div v-else class="image-error">
          <div class="error-icon">📷</div>
          <div class="error-text">图片加载失败</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {computed, ref, onMounted, onUnmounted} from 'vue'
import { useRouter } from 'vue-router'
import { chatApi } from '@/apis/auth_api'
import { message } from 'ant-design-vue'

const props = defineProps({
  reference: {
    type: [String, Object],
    default: null
  }
})

// 折叠状态 - 默认折叠（不显示）
const isCollapsed = ref(true)

// 图片模态框状态
const imageModalVisible = ref(false)
const currentImageId = ref('')
const currentImageTitle = ref('')
const imageLoading = ref(false)
const imageError = ref(false)

// 切换折叠状态
const toggleCollapse = () => {
  isCollapsed.value = !isCollapsed.value
}

// 打开图片模态框
const openImageModal = (imageId, title) => {
  currentImageId.value = imageId
  currentImageTitle.value = title || '图片'
  imageModalVisible.value = true
  imageLoading.value = true
  imageError.value = false
}

// 关闭图片模态框
const closeImageModal = () => {
  imageModalVisible.value = false
  currentImageId.value = ''
  currentImageTitle.value = ''
  imageLoading.value = false
  imageError.value = false
}

// 图片加载完成
const onImageLoad = () => {
  imageLoading.value = false
}

// 图片加载错误
const onImageError = () => {
  imageLoading.value = false
  imageError.value = true
}

// 键盘事件处理
const handleKeydown = (event) => {
  if (event.key === 'Escape' && imageModalVisible.value) {
    closeImageModal()
  }
}

// 监听键盘事件
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

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
  return `http://192.168.1.118:7080/v1/document/image/${imageId}`
}

// 下载文件
const openFilePreview = async (chunk) => {
  try {
    // 从chunk中获取必要的信息
    const datasetId = chunk.dataset_id || chunk.db_id || 'default'
    const documentId = chunk.document_id
    const documentName = chunk.document_name
    
    // 显示加载提示
    message.loading('正在准备下载...', 0)
    
    // 调用API下载文档
    const response = await chatApi.downloadDocument(datasetId, documentId)

    console.log('下载API响应:', response)
    // 关闭加载提示
    message.destroy()
    
    if (response && response.url) {
      // 如果有headers信息，说明需要特殊认证
      if (response.headers) {
        // 创建一个带有认证头的请求
        const downloadWithAuth = async () => {
          try {
            const authResponse = await fetch(response.url, {
              method: 'GET',
              headers: response.headers
            })
            
            if (authResponse.ok) {
              // 获取文件blob
              const blob = await authResponse.blob()
              
              // 创建下载链接
              const url = window.URL.createObjectURL(blob)
              const link = document.createElement('a')
              link.href = url
              link.download = documentName || 'document'
              document.body.appendChild(link)
              link.click()
              document.body.removeChild(link)
              
              // 清理URL对象
              window.URL.revokeObjectURL(url)
              
              message.success('文件下载成功')
            } else {
              throw new Error(`下载失败: ${authResponse.status}`)
            }
          } catch (error) {
            console.error('认证下载失败:', error)
            message.error('下载失败: ' + error.message)
          }
        }
        
        // 执行认证下载
        downloadWithAuth()
      } else {
        // 没有headers，直接打开链接
        if (response.url.startsWith('http')) {
          window.open(response.url, '_blank')
          message.success('下载链接已打开')
        } else {
          const downloadUrl = response.url.startsWith('/') ? response.url : `/${response.url}`
          window.open(downloadUrl, '_blank')
          message.success('下载链接已打开')
        }
      }
    } else {
      message.error('下载失败：未获取到下载链接')
    }
  } catch (error) {
    // 关闭加载提示
    message.destroy()
    console.error('下载失败:', error)
    message.error('下载失败: ' + (error.message || '未知错误'))
  }
}
</script>

<style lang="less" scoped>
.reference-display {
  margin-top: 16px;
  padding: 0;
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
          
          &.clickable {
            cursor: pointer;
            color: var(--main-600);
            transition: color 0.2s ease;
            
            &:hover {
              color: var(--main-700);
              text-decoration: underline;
            }
            
            &::after {
              content: ' ⬇️';
              font-size: 12px;
              opacity: 0.7;
            }
          }
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
        cursor: pointer;
        transition: transform 0.2s ease, box-shadow 0.2s ease;

        &:hover {
          transform: scale(1.02);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
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

// 图片模态框样式
.image-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.8);
  z-index: 1000;
  display: flex;
  justify-content: center;
  align-items: center;
  animation: fadeIn 0.3s ease;

  .image-modal-content {
    background: white;
    border-radius: 12px;
    max-width: 90vw;
    max-height: 90vh;
    overflow: hidden;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    animation: slideInUp 0.3s ease;

    .image-modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      border-bottom: 1px solid var(--gray-200);
      background: var(--gray-50);

      .image-modal-title {
        font-weight: 600;
        color: var(--gray-800);
        font-size: 16px;
      }

      .image-modal-close {
        background: none;
        border: none;
        font-size: 24px;
        color: var(--gray-600);
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        transition: background-color 0.2s ease;

        &:hover {
          background-color: var(--gray-200);
          color: var(--gray-800);
        }
      }
    }

    .image-modal-body {
      padding: 20px;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 200px;
      position: relative;

      .image-modal-image {
        max-width: 100%;
        max-height: 70vh;
        object-fit: contain;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }

      &::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 40px;
        height: 40px;
        border: 3px solid var(--gray-300);
        border-top-color: var(--main-500);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        display: none;
      }

      &.loading::before {
        display: block;
      }

      .image-error {
        text-align: center;
        color: var(--gray-600);
        padding: 40px 20px;

        .error-icon {
          font-size: 48px;
          margin-bottom: 16px;
          opacity: 0.5;
        }

        .error-text {
          font-size: 14px;
        }
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

  .image-modal-overlay {
    .image-modal-content {
      max-width: 95vw;
      max-height: 95vh;
      margin: 10px;

      .image-modal-header {
        padding: 12px 16px;

        .image-modal-title {
          font-size: 14px;
        }

        .image-modal-close {
          font-size: 20px;
        }
      }

      .image-modal-body {
        padding: 16px;

        .image-modal-image {
          max-height: 60vh;
        }
      }
    }
  }
}
</style> 