<template>
  <div class="reference-sidebar-overlay" v-if="isOpen" @click="closeSidebar">
    <div class="reference-sidebar" @click.stop>
      <div class="sidebar-header">
        <div class="header-title">📚 参考知识</div>
        <div class="header-actions">
          <div class="close-btn" @click="closeSidebar">
            <CloseOutlined />
          </div>
        </div>
      </div>
      <div class="sidebar-content">
        <ReferenceDisplay v-if="referenceData" :reference="referenceData" />
        <div v-else class="empty-content">
          <div class="empty-icon">📚</div>
          <div class="empty-text">暂无参考信息</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { CloseOutlined } from '@ant-design/icons-vue'
import ReferenceDisplay from '@/components/ReferenceDisplay.vue'

const props = defineProps({
  reference: {
    type: [String, Object],
    default: null
  },
  isOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close-sidebar'])

// 关闭侧边栏
const closeSidebar = () => {
  emit('close-sidebar')
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
</script>

<style lang="less" scoped>
.reference-sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
  animation: fadeIn 0.3s ease;

  .reference-sidebar {
    width: 400px;
    max-width: 90vw;
    height: 100%;
    background-color: white;
    box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
    animation: slideInRight 0.3s ease;

    .sidebar-header {
      height: var(--header-height);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 16px;
      border-bottom: 1px solid #e8e8e8;
      background-color: white;

      .header-title {
        font-weight: 500;
        font-size: 16px;
        color: var(--gray-900);
      }

      .header-actions {
        .close-btn {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 4px;
          cursor: pointer;
          color: var(--gray-600);
          transition: all 0.2s ease;

          &:hover {
            background-color: var(--gray-100);
            color: var(--gray-800);
          }
        }
      }
    }

    .sidebar-content {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      background-color: var(--gray-50);

      .empty-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 200px;
        color: var(--gray-500);

        .empty-icon {
          font-size: 48px;
          margin-bottom: 16px;
          opacity: 0.5;
        }

        .empty-text {
          font-size: 14px;
        }
      }
    }
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .reference-sidebar-overlay {
    .reference-sidebar {
      width: 320px;
    }
  }
}

@media (max-width: 520px) {
  .reference-sidebar-overlay {
    .reference-sidebar {
      width: 100vw;
    }
  }
}
</style> 