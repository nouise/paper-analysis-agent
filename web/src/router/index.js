import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import Home from '../views/HomeView.vue'
import KnowledgeBase from '../views/KnowledgeBase.vue'
import History from '../views/History.vue'
import WeChatEditor from '../views/WeChatEditor.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'Home',
        component: Home,
        meta: {
          title: 'Research Atelier',
          icon: '◈'
        }
      },
      {
        path: 'history',
        name: 'History',
        component: History,
        meta: {
          title: 'History Archive',
          icon: '◉'
        }
      },
      {
        path: 'knowledge',
        name: 'KnowledgeBase',
        component: KnowledgeBase,
        meta: {
          title: 'Knowledge Library',
          icon: '◆'
        }
      },
      {
        path: 'wechat',
        name: 'WeChatEditor',
        component: WeChatEditor,
        meta: {
          title: 'WeChat Publisher',
          icon: '✎'
        }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
