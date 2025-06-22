import { ref } from "vue";
import { apiFetch } from "../lib/api.js";
import { fetchEphemeralSession } from "../lib/api.js";

/**
 * Tiny wrapper around the WebRTC connection flow described in the OpenAI docs.
 * It exposes a handful of reactive refs that components can bind to.
 */
export function useRealtime() {
  const status = ref("idle"); // idle | connecting | live | error
  const messages = ref([]); // raw events from data-channel
  // activity state: 'none' | 'user' | 'assistant'
  const activity = ref('none');
  const pcRef = ref(null);
  const dcRef = ref(null);

  async function connect({ voice } = {}) {
    try {
      status.value = "connecting";

      // 1) Fetch an ephemeral key + session params from our backend.
      const session = await fetchEphemeralSession({ voice });
      const EPHEMERAL_KEY = session.client_secret.value;

      // 2) Create peer connection & data channel.
      const pc = new RTCPeerConnection();
      pcRef.value = pc;

      // Forward remote audio to <audio> element – we create one lazily.
      pc.ontrack = (e) => {
        let el = document.querySelector("#remote-audio");
        if (!el) {
          el = document.createElement("audio");
          el.id = "remote-audio";
          el.autoplay = true;
          document.body.appendChild(el);
        }
        el.srcObject = e.streams[0];
      };

      // Local microphone.
      const ms = await navigator.mediaDevices.getUserMedia({ audio: true });
      pc.addTrack(ms.getTracks()[0]);

      // Data channel for events.
      const dc = pc.createDataChannel("oai-events");
      dcRef.value = dc;
      dc.addEventListener("message", async (e) => {
        // Debug log raw data-channel message
        console.log("[RTC_EVENT_RAW]", e.data);
        let parsed;
        try {
          parsed = JSON.parse(e.data);
        messages.value.push(parsed);
        // Update speaking activity based on realtime events
        if (parsed.type === 'input_audio_buffer.speech_started') {
          activity.value = 'user';
        } else if (parsed.type === 'input_audio_buffer.speech_stopped') {
          activity.value = 'none';
        } else if (parsed.type === 'output_audio_buffer.started') {
          activity.value = 'assistant';
        } else if (parsed.type === 'output_audio_buffer.stopped') {
          activity.value = 'none';
        }
          console.log('[RTC_PARSED]', parsed);
        } catch (_) {
          messages.value.push(e.data);
          return;
        }
        // Detect completed function_call events from the Realtime API
        // Support both legacy 'function_call' and the newer 'response.function_call_arguments.done'
        const isFunctionDone = (parsed.type === 'function_call')
          || (parsed.type === 'response.function_call_arguments.done');
        if (isFunctionDone && parsed.name && parsed.arguments) {
          console.log('[RTC_FUNCTION_CALL]', parsed.name, parsed.arguments, 'dcRef:', !!dcRef.value);
          // Parse arguments if they arrive as a JSON string
          let funcArgs = parsed.arguments;
          if (typeof funcArgs === 'string') {
            try {
              funcArgs = JSON.parse(funcArgs);
            } catch (parseErr) {
              console.error('Invalid function arguments JSON:', funcArgs);
              return;
            }
          }
          try {
            // Call backend to execute function and get result
            const res = await apiFetch("/realtime/function-call", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ name: parsed.name, arguments: funcArgs }),
            });
            const json = await res.json();
            console.log("[FunctionCall] executed:", parsed.name, json);
            if (dcRef.value && json.status === 'ok') {
              let summaryText;
              if (parsed.name === 'create_move') {
                const { id, origin_country, destination_country, start_date } = json.result;
                summaryText = `Your move has been created: ID ${id}, from ${origin_country} to ${destination_country}, start date ${start_date}.`;
              } else if (parsed.name === 'create_task') {
                const { id, title } = json.result;
                summaryText = `Your task has been created: ID ${id}, title ${title}.`;
              } else if (parsed.name === 'external_api_call') {
                const { status_code, body } = json.result;
                summaryText = `External API ${parsed.arguments.method} ${parsed.arguments.endpoint} returned status ${status_code}. Response: ${JSON.stringify(body)}`;
              }
              if (summaryText) {
                const convEvent = {
                  type: 'conversation.item.create',
                  item: {
                    type: 'message',
                    role: 'assistant',
                    content: [{ type: 'text', text: summaryText }]
                  }
                };
                const convJson = JSON.stringify(convEvent);
                console.log('[RTC_EVENT_JSON]', convJson);
                dcRef.value.send(convJson);
              }
            }
          } catch (err) {
            console.error("Failed to execute/log function call:", err);
          }
        }
      });

      // 3) SDP handshake.
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      const baseUrl = "https://api.openai.com/v1/realtime";
      const model = "gpt-4o-realtime-preview-2025-06-03";

      const sdpRes = await fetch(`${baseUrl}?model=${model}`, {
        method: "POST",
        body: offer.sdp,
        headers: {
          Authorization: `Bearer ${EPHEMERAL_KEY}`,
          "Content-Type": "application/sdp",
        },
      });

      if (!sdpRes.ok) throw new Error("Failed to exchange SDP with OpenAI");

      const answer = { type: "answer", sdp: await sdpRes.text() };
      await pc.setRemoteDescription(answer);

      status.value = "live";
    } catch (err) {
      console.error(err);
      status.value = "error";
    }
  }

  function disconnect() {
    if (pcRef.value) {
      pcRef.value.close();
    }
    status.value = "idle";
  }

  return { status, messages, activity, connect, disconnect };
}
