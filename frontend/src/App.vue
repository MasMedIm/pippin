<template>
  <div class="app-container">
    <div class="app-header">
      <img :src="mainImage" alt="pippin branding" class="branding-image" />
    </div>
    <div class="app-main">
      <div class="card realtime-demo">
        
        <div class="button-group">
          <button
            class="btn btn-primary"
            @click="onConnect"
            :disabled="rtc.status === 'connecting' || rtc.status === 'live'"
          >
            {{ rtc.status === 'live' ? 'Connected' : 'Connect' }}
          </button>
          <button
            v-if="rtc.status === 'live'"
            class="btn btn-secondary"
            @click="onDisconnect"
          >
            Disconnect
          </button>
        </div>
        <div class="function-calls">
          <h3>Opentrons FLEX Calls</h3>
          <ul>
            <li v-for="(call, idx) in functionCalls" :key="idx">
              <strong>{{ call.name }}</strong>: {{ JSON.stringify(call.arguments) }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRealtime } from "./composables/useRealtime.js";
import mainImage from "./assets/main-image.png";

// WebRTC hook
const rtc = useRealtime();

function onConnect() {
  rtc.connect();
}

function onDisconnect() {
  rtc.disconnect();
}

// Show only completed function_call events
const functionCalls = computed(() =>
  Array.isArray(rtc.messages?.value)
    ? rtc.messages.value.filter((m) => m.name)
    : []
);
</script>

<style scoped>
/* Layout containers */
.app-container {
  font-family: Arial, Helvetica, sans-serif;
  max-width: 800px;
  margin: 2rem auto;
  background-color: #f5f5f5;
  padding: 1rem;
  border-radius: 0.5rem;
}
.app-header {
  text-align: center;
  margin-bottom: 1rem;
}
.app-main {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Card component */
.card {
  background: #ffffff;
  border-radius: 0.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 1.5rem;
}


/* Button group */
.button-group {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  margin-bottom: 1rem;
}
.error {
  color: red;
  margin-top: 1rem;
}

.healthy {
  color: green;
}

.unhealthy {
  color: red;
}
.log {
  background: #f9f9f9;
  padding: 1rem;
  max-height: 300px;
  overflow: auto;
  text-align: left;
}
/* Button styles */
.btn {
  border: none;
  border-radius: 0.375rem;
  font-size: 1rem;
  padding: 0.75rem 1.5rem;
  margin: 0.5rem;
  cursor: pointer;
  transition: background-color 0.2s ease-in-out, transform 0.1s ease;
}
.btn:hover:not(:disabled) {
  transform: translateY(-1px);
}
.btn:disabled {
  background-color: #a3a3a3;
  cursor: not-allowed;
}
.btn-primary {
  background-color: #2B9C94;
  color: #fff;
}
.btn-primary:hover:not(:disabled) {
  background-color: #309C8F;
}
.btn-secondary {
  background-color: #e5e7eb;
  color: #374151;
}
.btn-secondary:hover:not(:disabled) {
  background-color: #d1d5db;
}
/* Branding image */
.branding-image {
  display: block;
  margin: 1.5rem auto;
  width: 300px;
  max-width: 80%;
  height: auto;
}

/* Function calls list */
.function-calls {
  margin-top: 1rem;
  text-align: left;
}
.function-calls ul {
  list-style: disc inside;
  margin: 0;
  padding: 0;
}
</style>
