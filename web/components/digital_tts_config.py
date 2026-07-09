# Copyright (C) 2025 AIDC-AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Style configuration components for web UI (middle column)
"""

import os
from pathlib import Path

import streamlit as st
from loguru import logger

from web.i18n import tr, get_language
from web.utils.async_helpers import run_async
from pixelle_video.config import config_manager


def render_style_config(pixelle_video):
    """Render style configuration section (middle column)"""
    # TTS Section (moved from left column)
    # ====================================================================
    with st.container(border=True):
        st.markdown(f"**{tr('section.tts')}**")
        
        with st.expander(tr("help.feature_description"), expanded=False):
            st.markdown(f"**{tr('help.what')}**")
            st.markdown(tr("tts.what"))
            st.markdown(f"**{tr('help.how')}**")
            st.markdown(tr("tts.how"))
        
        # Get TTS config
        comfyui_config = config_manager.get_comfyui_config()
        tts_config = comfyui_config["tts"]
        
        # TTS mode is always local
        tts_mode = "local"
        st.caption(tr("tts.mode.local_hint"))
        
        # ================================================================
        # Local Mode UI
        # ================================================================
        # Import voice configuration
        from pixelle_video.tts_voices import EDGE_TTS_VOICES, get_voice_display_name
        
        # Get saved voice from config
        local_config = tts_config.get("local", {})
        saved_voice = local_config.get("voice", "zh-CN-YunjianNeural")
        saved_speed = local_config.get("speed", 1.2)
        
        # Build voice options with i18n
        voice_options = []
        voice_ids = []
        default_voice_index = 0
        
        for idx, voice_config in enumerate(EDGE_TTS_VOICES):
            voice_id = voice_config["id"]
            display_name = get_voice_display_name(voice_id, tr, get_language())
            voice_options.append(display_name)
            voice_ids.append(voice_id)
            
            # Set default index if matches saved voice
            if voice_id == saved_voice:
                default_voice_index = idx
        
        # Two-column layout: Voice | Speed
        voice_col, speed_col = st.columns([1, 1])
        
        with voice_col:
            # Voice selector
            selected_voice_display = st.selectbox(
                tr("tts.voice_selector"),
                voice_options,
                index=default_voice_index,
                key="digital_tts_local_voice"
            )
            
            # Get actual voice ID
            selected_voice_index = voice_options.index(selected_voice_display)
            selected_voice = voice_ids[selected_voice_index]
        
        with speed_col:
            # Speed slider
            tts_speed = st.slider(
                tr("tts.speed"),
                min_value=0.5,
                max_value=2.0,
                value=saved_speed,
                step=0.1,
                format="%.1fx",
                key="digital_tts_local_speed"
            )
            st.caption(tr("tts.speed_label", speed=f"{tts_speed:.1f}x"))
        
        # Variables for video generation
        tts_workflow_key = None
        ref_audio_path = None
        
        # ================================================================
        # TTS Preview
        # ================================================================
        with st.expander(tr("tts.preview_title"), expanded=False):
            # Preview text input
            preview_text = st.text_input(
                tr("tts.preview_text"),
                value="大家好，这是一段测试语音。",
                placeholder=tr("tts.preview_text_placeholder"),
                key="digital_tts_preview_text"
            )
            
            # Preview button
            if st.button(tr("tts.preview_button"), key="gidital_preview_tts", use_container_width=True):
                with st.spinner(tr("tts.previewing")):
                    try:
                        # Build TTS params (local mode only)
                        tts_params = {
                            "text": preview_text,
                            "inference_mode": "local",
                            "voice": selected_voice,
                            "speed": tts_speed,
                        }
                    
                        audio_path = run_async(pixelle_video.tts(**tts_params))
                        
                        # Play the audio
                        if audio_path:
                            st.success(tr("tts.preview_success"))
                            if os.path.exists(audio_path):
                                st.audio(audio_path, format="audio/mp3")
                            elif audio_path.startswith('http'):
                                st.audio(audio_path)
                            else:
                                st.error("Failed to generate preview audio")
                            
                            # Show file path
                            st.caption(f"📁 {audio_path}")
                        else:
                            st.error("Failed to generate preview audio")
                    except Exception as e:
                        st.error(tr("tts.preview_failed", error=str(e)))
                        logger.exception(e)
    
    # Return all style configuration parameters (local TTS only)
    return {
        "tts_inference_mode": "local",
        "tts_voice": selected_voice,
        "tts_speed": tts_speed,
        "tts_workflow": None,
        "ref_audio": None,
    }