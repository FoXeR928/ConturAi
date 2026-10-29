import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';
import { PluginProvider } from './plugins/PluginContext'; // <-- Импорт

const rootElement = document.getElementById('root')!;
const root = ReactDOM.createRoot(rootElement);

root.render(
  <React.StrictMode>
    <BrowserRouter>
      {/* PluginProvider оборачивает App, чтобы плагины загрузились до рендера страниц */}
      <PluginProvider>
        <App />
      </PluginProvider>
    </BrowserRouter>
  </React.StrictMode>
);