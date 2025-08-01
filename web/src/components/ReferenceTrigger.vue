<template>
  <div class="reference-trigger" v-if="hasValidReference">
    <button class="trigger-btn" @click="openReference">
      <FileTextOutlined />
      <span class="trigger-text">查看参考信息</span>
<!--      <span class="reference-count">{{ referenceCount }}</span>-->
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { FileTextOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  reference: {
    type: [String, Object],
    default: null
  }
})

const emit = defineEmits(['open-reference'])

// 检查是否有有效的引用数据
const hasValidReference = computed(() => {
  if (!props.reference) return false

  // 处理空对象的情况
  if (props.reference === null || props.reference === undefined) return false

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
    if (!parsedData || typeof parsedData !== 'object') return false

    // 检查是否为空对象 {}
    if (Object.keys(parsedData).length === 0) return false

    // 检查是否有有效的chunks数据
    if (!parsedData.chunks || !Array.isArray(parsedData.chunks) || parsedData.chunks.length === 0) {
      return false
    }

    return true
  } catch (error) {
    console.error('解析引用数据失败:', error)
    return false
  }
})

// 获取引用数量
const referenceCount = computed(() => {
  if (!props.reference) return 0

  try {
    let parsedData
    if (typeof props.reference === 'string') {
      parsedData = JSON.parse(props.reference)
    } else {
      parsedData = props.reference
    }

    if (parsedData && parsedData.chunks && Array.isArray(parsedData.chunks)) {
      return parsedData.chunks.length
    }
    return 0
  } catch (error) {
    return 0
  }
})

// 打开参考信息
const openReference = () => {
  emit('open-reference', props.reference)
}
</script>

<style lang="less" scoped>
.reference-trigger {
  margin-top: 0px;
  margin-bottom: 10px;
  display: flex;
  justify-content: flex-start;

  .trigger-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background-color: var(--gray-100);
    border: 1px solid var(--gray-300);
    border-radius: 8px;
    color: var(--gray-700);
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);

    &:hover {
      background-color: var(--gray-200);
      border-color: var(--gray-400);
      color: var(--gray-800);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
      transform: translateY(-1px);
    }

    &:active {
      background-color: var(--gray-300);
      transform: translateY(0);
    }

    .trigger-text {
      font-size: 14px;
    }

    .reference-count {
      background-color: var(--gray-200);
      color: var(--gray-700);
      padding: 2px 6px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 600;
      min-width: 20px;
      text-align: center;
    }
  }
}
</style> 