"""
Call Copilot - Core Engine
Audio Capture -> Deepgram STT -> LLM (streaming) -> Response
With bridge phrases, cancel-on-new-speech, and smart silence detection.
"""
import asyncio
import json
import os
import sys
import time
import threading
import queue
import datetime
import random
import numpy as np
import websockets
import winsound
# Multi-provider LLM support
def _init_llm_client(config):
    provider = config.get("llm_provider", "groq")
    if provider == "groq":
        from groq import Groq
        return "groq", Groq(api_key=config["groq_api_key"])
    elif provider == "claude":
        import anthropic
        return "claude", anthropic.Anthropic(api_key=config["claude_api_key"])
    elif provider == "openai":
        from openai import OpenAI
        return "openai", OpenAI(api_key=config["openai_api_key"])
    elif provider == "gemini":
        from google import genai
        return "gemini", genai.Client(api_key=config["gemini_api_key"])
    elif provider == "claude_bedrock":
        import boto3
        client = boto3.client(
            "bedrock-runtime",
            region_name=config.get("aws_region", "us-east-1"),
            aws_access_key_id=config["aws_access_key_id"],
            aws_secret_access_key=config["aws_secret_access_key"],
        )
        return "claude_bedrock", client
    else:
        from groq import Groq
        return "groq", Groq(api_key=config["groq_api_key"])


# Bridge phrases - shown instantly when silence detected, before AI thinks
BRIDGE_PHRASES = [
    "Right, so...",
    "Okay so...",
    "Got it...",
    "Yeah...",
    "Sure...",
    "Right...",
    "Hmm...",
    "So...",
    "Okay...",
    "I hear you...",
]


class CallCopilotEngine:
    def __init__(self, config, system_prompt, on_transcript=None, on_response=None,
                 on_status=None, on_interim=None, on_error=None, on_bridge=None,
                 on_response_chunk=None):
        self.config = config
        self.system_prompt = system_prompt
        self.llm_provider, self.llm_client = _init_llm_client(config)

        # Fallback: always keep Groq ready as backup
        if self.llm_provider != "groq" and config.get("groq_api_key"):
            try:
                from groq import Groq
                self.fallback_provider = "groq"
                self.fallback_client = Groq(api_key=config["groq_api_key"])
            except:
                self.fallback_provider = None
                self.fallback_client = None
        else:
            self.fallback_provider = None
            self.fallback_client = None

        # Callbacks
        self.on_transcript = on_transcript or (lambda t, f: None)
        self.on_response = on_response or (lambda r, ms: None)
        self.on_status = on_status or (lambda s: None)
        self.on_interim = on_interim or (lambda t: None)
        self.on_error = on_error or (lambda e: None)
        self.on_bridge = on_bridge or (lambda b: None)  # NEW: bridge phrase callback
        self.on_response_chunk = on_response_chunk or (lambda c: None)  # NEW: streaming chunk

        # State
        self.audio_queue = queue.Queue()
        self.audio_mode = "loopback"
        self.conversation = []
        self.accumulated = []
        self.last_speech_time = 0.0
        self.is_generating = False
        self.cancel_generation = False  # NEW: flag to abort generation mid-stream
        self.running = False
        self.target_sr = 16000
        self.pre_call_context = ""
        self.call_log = []
        self.call_start_time = None
        self.response_count = 0
        self.total_audio_bytes = 0
        self._last_bridge_idx = -1  # track last bridge phrase used
        self._utterance_end_pending = False  # NEW: debounce UtteranceEnd

    def set_precall_context(self, context):
        self.pre_call_context = context.strip()

    def _get_bridge_phrase(self):
        """Get a random bridge phrase, avoiding repeats."""
        idx = random.randint(0, len(BRIDGE_PHRASES) - 1)
        while idx == self._last_bridge_idx and len(BRIDGE_PHRASES) > 1:
            idx = random.randint(0, len(BRIDGE_PHRASES) - 1)
        self._last_bridge_idx = idx
        return BRIDGE_PHRASES[idx]

    def get_llm_response_streaming(self, client_said):
        """Stream LLM response token-by-token. Returns (full_reply, latency_ms)."""
        prompt = ('Client just said: "' + client_said + '"\n'
                  'What should I say back? Give the exact words to speak. '
                  'Do NOT include any thinking, reasoning, or notes -- ONLY the words to say out loud. '
                  'Keep it to 1-2 sentences max.')

        self.conversation.append({"role": "user", "content": prompt})

        messages = [{"role": "system", "content": self._build_system_prompt()}]
        messages += self.conversation[-12:]

        try:
            t0 = time.time()
            full_reply = self._call_llm_streaming(messages)
            ms = (time.time() - t0) * 1000

            if full_reply is None:
                # Generation was cancelled
                self.conversation.pop()  # remove the unanswered user message
                return None, 0

            # Clean up
            if full_reply.startswith('"') and full_reply.endswith('"'):
                full_reply = full_reply[1:-1]
            import re
            full_reply = re.sub(r'<think>.*?</think>', '', full_reply, flags=re.DOTALL).strip()

            self.conversation.append({"role": "assistant", "content": full_reply})

            self.call_log.append({
                "time": time.time() - (self.call_start_time or time.time()),
                "type": "response",
                "client_said": client_said,
                "response": full_reply,
                "latency_ms": round(ms),
            })

            return full_reply, ms
        except Exception as e:
            err_msg = str(e)
            # Auto-fallback to Groq
            if self.fallback_client and self.fallback_provider:
                try:
                    self.on_status("Primary failed, using backup...")
                    t0 = time.time()
                    temp = self.config["temperature"]
                    max_tok = self.config["max_response_tokens"]
                    r = self.fallback_client.chat.completions.create(
                        model=self.config.get("groq_model", "llama-3.3-70b-versatile"),
                        messages=messages, temperature=temp, max_tokens=max_tok,
                    )
                    reply = r.choices[0].message.content.strip()
                    ms = (time.time() - t0) * 1000
                    import re
                    reply = re.sub(r'<think>.*?</think>', '', reply, flags=re.DOTALL).strip()
                    if reply.startswith('"') and reply.endswith('"'):
                        reply = reply[1:-1]
                    self.conversation.append({"role": "assistant", "content": reply})
                    self.call_log.append({
                        "time": time.time() - (self.call_start_time or time.time()),
                        "type": "response_fallback",
                        "client_said": client_said,
                        "response": reply,
                        "latency_ms": round(ms),
                        "primary_error": err_msg[:80],
                    })
                    return reply, ms
                except Exception as e2:
                    self.on_error(f"Both LLMs failed: {str(e2)[:60]}")
                    return None, 0
            else:
                self.on_error(f"LLM Error: {err_msg[:100]}")
                return None, 0

    # Keep old non-streaming method as fallback
    def get_llm_response(self, client_said):
        return self.get_llm_response_streaming(client_said)

    def _build_system_prompt(self):
        prompt = self.system_prompt
        if self.pre_call_context:
            prompt += "\n\nPRE-CALL BRIEFING:\n" + self.pre_call_context
        return prompt

    def _call_llm_streaming(self, messages):
        """Call LLM with streaming and emit chunks via on_response_chunk. Returns full text or None if cancelled."""
        temp = self.config["temperature"]
        max_tok = self.config["max_response_tokens"]
        chunks = []
        first_chunk = True

        if self.llm_provider == "groq":
            stream = self.llm_client.chat.completions.create(
                model=self.config["groq_model"],
                messages=messages, temperature=temp, max_tokens=max_tok,
                stream=True,
            )
            for chunk in stream:
                if self.cancel_generation:
                    return None
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    text = delta.content
                    chunks.append(text)
                    if first_chunk:
                        self.on_status("Speaking...")
                        first_chunk = False
                    self.on_response_chunk(text)
            return "".join(chunks).strip()

        elif self.llm_provider == "claude":
            sys_msg = ""
            user_msgs = []
            for m in messages:
                if m["role"] == "system":
                    sys_msg = m["content"]
                else:
                    user_msgs.append(m)
            with self.llm_client.messages.stream(
                model=self.config["claude_model"],
                system=sys_msg,
                messages=user_msgs,
                max_tokens=max_tok, temperature=temp,
            ) as stream:
                for text in stream.text_stream:
                    if self.cancel_generation:
                        return None
                    chunks.append(text)
                    if first_chunk:
                        self.on_status("Speaking...")
                        first_chunk = False
                    self.on_response_chunk(text)
            return "".join(chunks).strip()

        elif self.llm_provider == "openai":
            stream = self.llm_client.chat.completions.create(
                model=self.config["openai_model"],
                messages=messages, temperature=temp, max_tokens=max_tok,
                stream=True,
            )
            for chunk in stream:
                if self.cancel_generation:
                    return None
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    text = delta.content
                    chunks.append(text)
                    if first_chunk:
                        self.on_status("Speaking...")
                        first_chunk = False
                    self.on_response_chunk(text)
            return "".join(chunks).strip()

        elif self.llm_provider == "claude_bedrock":
            sys_msg = ""
            user_msgs = []
            for m in messages:
                if m["role"] == "system":
                    sys_msg = m["content"]
                else:
                    user_msgs.append({"role": m["role"], "content": [{"text": m["content"]}]})
            response = self.llm_client.converse_stream(
                modelId=self.config["bedrock_model"],
                system=[{"text": sys_msg}] if sys_msg else [],
                messages=user_msgs,
                inferenceConfig={"maxTokens": max_tok, "temperature": temp},
            )
            event_stream = response.get("stream", [])
            for event in event_stream:
                if self.cancel_generation:
                    return None
                if "contentBlockDelta" in event:
                    delta = event["contentBlockDelta"].get("delta", {})
                    text = delta.get("text", "")
                    if text:
                        chunks.append(text)
                        if first_chunk:
                            self.on_status("Speaking...")
                            first_chunk = False
                        self.on_response_chunk(text)
            return "".join(chunks).strip()

        elif self.llm_provider == "gemini":
            sys_msg = ""
            user_text = ""
            for m in messages:
                if m["role"] == "system":
                    sys_msg = m["content"]
                elif m["role"] == "user":
                    user_text = m["content"]
            r = self.llm_client.models.generate_content(
                model=self.config["gemini_model"],
                contents=user_text,
                config={"system_instruction": sys_msg, "temperature": temp, "max_output_tokens": max_tok},
            )
            text = r.text.strip()
            self.on_response_chunk(text)
            return text

        return "Error: Unknown LLM provider"

    # Keep the old _call_llm for backward compat
    def _call_llm(self, messages):
        return self._call_llm_streaming(messages)

    def find_microphone_device(self):
        """Find the default microphone for capturing room audio (phone on speaker)."""
        import pyaudiowpatch as pyaudio
        p = pyaudio.PyAudio()
        try:
            default = p.get_default_input_device_info()
            sr = min(int(default["defaultSampleRate"]), 16000)
            ch = 1
            idx = default["index"]
            name = default["name"]
            p.terminate()
            return idx, sr, ch, "MIC: " + name
        except Exception as e:
            p.terminate()
            return None, None, None, "No microphone found: " + str(e)

    def find_loopback_device(self):
        import pyaudiowpatch as pyaudio
        p = pyaudio.PyAudio()

        wasapi = None
        for i in range(p.get_host_api_count()):
            info = p.get_host_api_info_by_index(i)
            if 'wasapi' in info['name'].lower():
                wasapi = info
                break

        if wasapi is None:
            p.terminate()
            return None, None, None, "WASAPI not available"

        default_out = p.get_device_info_by_index(wasapi['defaultOutputDevice'])
        default_name = default_out['name']

        target = None
        all_loopbacks = []
        for i in range(p.get_device_count()):
            d = p.get_device_info_by_index(i)
            if d.get('isLoopbackDevice', False):
                all_loopbacks.append(d)
                if default_name in d['name']:
                    target = d

        if target is None:
            for d in all_loopbacks:
                if 'realtek' in d['name'].lower():
                    target = d
                    break

        if target is None and all_loopbacks:
            target = all_loopbacks[0]

        if target is None:
            p.terminate()
            return None, None, None, "No loopback device found"

        sr = int(target['defaultSampleRate'])
        ch = target['maxInputChannels']
        idx = target['index']
        name = target['name']
        p.terminate()
        return idx, sr, ch, name

    def _audio_thread(self, dev_idx, sr, ch):
        import pyaudiowpatch as pyaudio
        p = pyaudio.PyAudio()
        try:
            stream = p.open(
                format=pyaudio.paInt16, channels=ch, rate=sr,
                input=True, input_device_index=dev_idx,
                frames_per_buffer=int(sr * 0.25)
            )
            while self.running:
                try:
                    data = stream.read(int(sr * 0.25), exception_on_overflow=False)
                    self.audio_queue.put((data, sr, ch))
                    self.total_audio_bytes += len(data)
                except Exception:
                    if self.running:
                        time.sleep(0.1)
            stream.stop_stream()
            stream.close()
        except Exception as e:
            self.on_error(f"Audio device error: {e}")
        finally:
            p.terminate()

    async def _generate_response(self):
        if not self.accumulated or self.is_generating:
            return
        self.is_generating = True
        self.cancel_generation = False
        text = " ".join(self.accumulated)
        self.accumulated.clear()

        # Skip very short utterances (likely noise / filler)
        words = text.split()
        if len(words) < 4:
            self.is_generating = False
            return

        # Skip pure filler responses
        filler_words = {"yeah", "yes", "okay", "ok", "right", "uh", "um", "hmm", "mhm", "yep", "sure", "hello", "hi"}
        clean_words = [w.strip(".,!?").lower() for w in words]
        if all(w in filler_words for w in clean_words):
            self.is_generating = False
            return

        # Show bridge phrase INSTANTLY (before AI starts thinking)
        bridge = self._get_bridge_phrase()
        self.on_bridge(bridge)

        self.on_status("Thinking...")

        loop = asyncio.get_event_loop()
        reply, ms = await loop.run_in_executor(None, self.get_llm_response_streaming, text)

        if reply and not self.cancel_generation:
            self.response_count += 1
            self.on_response(reply, ms)
            try:
                winsound.Beep(800, 100)
            except:
                pass

        self.on_status("Listening...")
        self.is_generating = False

    async def run(self):
        self.running = True
        self.call_start_time = time.time()
        self.call_log = []
        self.response_count = 0
        self.total_audio_bytes = 0

        self.on_status("Finding audio device...")
        if self.audio_mode == "microphone":
            dev, sr, ch, dev_name = self.find_microphone_device()
        else:
            dev, sr, ch, dev_name = self.find_loopback_device()
        if dev is None:
            self.on_error(f"Audio error: {dev_name}")
            self.on_status("Error - no audio device")
            self.running = False
            return

        self.on_status(f"Audio: {dev_name[:30]}")
        self.call_log.append({"type": "info", "device": dev_name, "sr": sr, "ch": ch})

        audio_t = threading.Thread(target=self._audio_thread, args=(dev, sr, ch), daemon=True)
        audio_t.start()
        time.sleep(0.3)

        self.on_status("Connecting...")
        url = (
            f"wss://api.deepgram.com/v1/listen?"
            f"model={self.config['stt_model']}&"
            f"language={self.config['language']}&"
            f"smart_format=true&interim_results=true&"
            f"utterance_end_ms={self.config['utterance_end_ms']}&"
            f"vad_events=true&encoding=linear16&"
            f"sample_rate={self.target_sr}&channels=1"
        )
        headers = {"Authorization": f"Token {self.config['deepgram_api_key']}"}

        reconnect_delay = 1
        while self.running:
            try:
                async with websockets.connect(
                    url, additional_headers=headers,
                    ping_interval=5, ping_timeout=20,
                    close_timeout=5
                ) as ws:
                    reconnect_delay = 1
                    self.on_status("Listening...")

                    async def sender():
                        while self.running:
                            n = 0
                            while not self.audio_queue.empty() and n < 25:
                                raw, rs, rc = self.audio_queue.get_nowait()
                                samples = np.frombuffer(raw, dtype=np.int16)
                                if rc > 1:
                                    samples = samples.reshape(-1, rc).mean(axis=1).astype(np.int16)
                                if rs != self.target_sr:
                                    f = samples.astype(np.float32)
                                    ratio = rs / self.target_sr
                                    idx = np.arange(0, len(f), ratio).astype(int)
                                    samples = f[idx[idx < len(f)]].astype(np.int16)
                                try:
                                    await ws.send(samples.tobytes())
                                except:
                                    return
                                n += 1
                            await asyncio.sleep(0.035)

                    async def receiver():
                        async for msg in ws:
                            if not self.running:
                                break
                            d = json.loads(msg)
                            msg_type = d.get("type", "")

                            if msg_type == "Results":
                                alts = d.get("channel", {}).get("alternatives", [])
                                if alts:
                                    txt = alts[0].get("transcript", "").strip()
                                    if txt:
                                        final = d.get("is_final", False)
                                        if final:
                                            self.on_transcript(txt, True)
                                            self.accumulated.append(txt)
                                            self.last_speech_time = time.time()
                                            self.call_log.append({
                                                "time": time.time() - self.call_start_time,
                                                "type": "transcript",
                                                "text": txt,
                                            })
                                            # Cancel current generation if client starts talking again
                                            if self.is_generating:
                                                self.cancel_generation = True
                                        else:
                                            self.on_interim(txt)
                                            # Also cancel on interim speech
                                            if self.is_generating and len(txt.split()) > 2:
                                                self.cancel_generation = True

                            elif msg_type == "UtteranceEnd":
                                # DON'T fire immediately - just mark it
                                # Let silence_monitor handle the actual trigger
                                self._utterance_end_pending = True

                    async def silence_monitor():
                        while self.running:
                            await asyncio.sleep(0.3)
                            trigger = self.config.get("silence_trigger_sec", 3.0)

                            if (self.accumulated and not self.is_generating
                                    and self.last_speech_time > 0
                                    and time.time() - self.last_speech_time > trigger):
                                await self._generate_response()

                    async def keepalive():
                        while self.running:
                            await asyncio.sleep(8)
                            try:
                                await ws.send(json.dumps({"type": "KeepAlive"}))
                            except:
                                return

                    tasks = [
                        asyncio.create_task(sender()),
                        asyncio.create_task(receiver()),
                        asyncio.create_task(silence_monitor()),
                        asyncio.create_task(keepalive()),
                    ]
                    try:
                        await asyncio.gather(*tasks)
                    except asyncio.CancelledError:
                        pass

            except websockets.exceptions.ConnectionClosed:
                if self.running:
                    self.on_status(f"Reconnecting ({reconnect_delay}s)...")
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, 10)

            except Exception as e:
                if self.running:
                    self.on_error(f"Connection error: {str(e)[:80]}")
                    self.on_status(f"Reconnecting ({reconnect_delay}s)...")
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, 10)

    def stop(self):
        self.running = False

    def save_call_log(self):
        if not self.call_log or not self.config.get("save_call_logs"):
            return None

        from src.config import ensure_log_dir
        log_dir = ensure_log_dir()
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(log_dir, f"call_{ts}.json")

        summary = {
            "timestamp": ts,
            "duration_sec": round(time.time() - self.call_start_time) if self.call_start_time else 0,
            "responses_generated": self.response_count,
            "audio_bytes": self.total_audio_bytes,
            "pre_call_context": self.pre_call_context,
            "events": self.call_log,
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            return filepath
        except Exception as e:
            print(f"Warning: Could not save call log: {e}")
            return None
