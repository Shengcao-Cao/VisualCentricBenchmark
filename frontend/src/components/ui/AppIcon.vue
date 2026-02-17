<template>
  <component
    :is="iconComponent"
    :class="['icon', spin ? 'spin' : '']"
    :size="size"
    :color="color"
    :stroke-width="strokeWidth"
    aria-hidden="true"
  />
</template>

<script setup lang="ts">
import { computed, type Component } from "vue";
import {
  Activity,
  Aperture,
  ArrowUp,
  Check,
  ChevronDown,
  History,
  LoaderCircle,
  Plus,
  Settings,
  Share2,
  TriangleRight,
  User
} from "lucide-vue-next";

type IconName =
  | "aperture"
  | "plus"
  | "settings"
  | "user"
  | "triangle-right"
  | "activity"
  | "share-2"
  | "arrow-up"
  | "chevron-down"
  | "check"
  | "loader"
  | "history";

const props = withDefaults(
  defineProps<{
    name: IconName;
    size?: number;
    color?: string;
    strokeWidth?: number;
    spin?: boolean;
  }>(),
  {
    size: 16,
    color: "currentColor",
    strokeWidth: 2,
    spin: false
  }
);

const iconMap: Record<IconName, Component> = {
  aperture: Aperture,
  plus: Plus,
  settings: Settings,
  user: User,
  "triangle-right": TriangleRight,
  activity: Activity,
  "share-2": Share2,
  "arrow-up": ArrowUp,
  "chevron-down": ChevronDown,
  check: Check,
  loader: LoaderCircle,
  history: History
};

const iconComponent = computed(() => iconMap[props.name]);
const size = computed(() => props.size);
const color = computed(() => props.color);
const strokeWidth = computed(() => props.strokeWidth);
const spin = computed(() => props.spin);
</script>

<style scoped>
.icon {
  display: inline-block;
}

.spin {
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>

