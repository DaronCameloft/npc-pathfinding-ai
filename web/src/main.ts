import { createApp } from 'vue'
import App from './App.vue'
import { conectarMotor } from './core/motor'
import { router } from './router'
import './styles/base.css'

createApp(App).use(router).mount('#app')
void conectarMotor()
