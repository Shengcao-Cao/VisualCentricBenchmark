import { createRouter, createWebHistory } from "vue-router";
import WorkspaceView from "../views/WorkspaceView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: "/", name: "workspace", component: WorkspaceView }]
});

