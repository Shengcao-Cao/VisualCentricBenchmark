import { createApp } from "vue";
import App from "./App.vue";
import { installProviders } from "./providers";
import "./styles.css";

const app = createApp(App);
installProviders(app);
app.mount("#app");

