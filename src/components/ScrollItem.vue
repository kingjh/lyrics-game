<template>
  <div class="scroll-wrapper">
    <div 
      :class="['scroll', {'broken': scroll.isBroken}]" 
      :style="{width: scroll.width + 'px'}"
    >
      <div 
        class="scroll-handle" 
        @mousedown="startDrag($event)"
        @touchstart="startDrag($event)"
      ></div>
      <div class="scroll-content font-weight-bold">{{ scroll.lyrics }}</div>
    </div>
    <div class="scroll-title">{{ scroll.name }}</div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue'

interface Scroll {
  name: string;
  lyrics: string;
  width: number;
  maxWidth: number;
  isBroken: boolean;
  visibleText: string;
  index: number;
}

const props = defineProps({
  scroll: {
    type: Object as () => Scroll,
    required: true
  },
  isGameOver: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['startDrag'])

const startDrag = (e: MouseEvent | TouchEvent) => {
  if (props.scroll.isBroken || props.isGameOver) return
  
  emit('startDrag', {
    event: e,
    index: props.scroll.index
  })
  
  e.preventDefault()
}
</script>

<style scoped>
.scroll-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  margin-bottom: 10px;
  justify-content: flex-end;
}

.scroll {
  position: relative;
  height: 40px;
  background: linear-gradient(to right, #e6e0fa, #d4c6f5);
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: width 0.3s ease;
  display: flex;
  align-items: center;
  padding-right: 10px;
  margin-left: auto;
  border: 1px solid #b39ddb;
}

.scroll.broken {
  background: linear-gradient(to right, #ffe0f0, #ffccd5);
  cursor: not-allowed;
  border: 1px solid #ff6b6b;
}

.scroll-title {
  position: absolute;
  width: 116px;
  height: 40px;
  padding: 8px;
  border-radius: 0 8px 8px 0;
  z-index: 2;
  background: radial-gradient(circle, #9575cd, #7e57c2);
  font-weight: bold;
  color: white;
  text-align: right;
}

.scroll-content {
  position: absolute;
  left: 28px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #424242;
}

.scroll-handle {
  width: 20px;
  height: 40px;
  background-color: #b39ddb;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  z-index: 3;
}

.scroll-handle::after {
  content: "≡";
  color: white;
  font-weight: bold;
}
</style> 