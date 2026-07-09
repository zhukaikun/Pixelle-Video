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
System settings component for web UI
"""

import streamlit as st

from web.i18n import tr, get_language
from web.utils.streamlit_helpers import safe_rerun
from pixelle_video.config import config_manager


def render_advanced_settings():
    """Render system configuration (required) with 2-column layout"""
    # Check if system is configured
    is_configured = config_manager.validate()
    
    # Expand if not configured, collapse if configured
    with st.expander(tr("settings.title"), expanded=not is_configured):
        # 2-column layout: LLM | Custom API Media Model
        llm_col, custom_media_col = st.columns(2)
        
        # ====================================================================
        # Column 1: LLM Settings
        # ====================================================================
        with llm_col:
            with st.container(border=True):
                st.markdown(f"**{tr('settings.llm.title')}**")
                
                # Quick preset selection
                from pixelle_video.llm_presets import get_preset_names, get_preset, find_preset_by_base_url_and_model
                
                # Custom at the end
                preset_names = get_preset_names() + ["Custom"]
                
                # Get current config
                current_llm = config_manager.get_llm_config()
                
                # Auto-detect which preset matches current config
                current_preset = find_preset_by_base_url_and_model(
                    current_llm["base_url"], 
                    current_llm["model"]
                )
                
                # Determine default index based on current config
                if current_preset:
                    # Current config matches a preset
                    default_index = preset_names.index(current_preset)
                else:
                    # Current config doesn't match any preset -> Custom
                    default_index = len(preset_names) - 1
                
                selected_preset = st.selectbox(
                    tr("settings.llm.quick_select"),
                    options=preset_names,
                    index=default_index,
                    help=tr("settings.llm.quick_select_help"),
                    key="llm_preset_select"
                )
                
                # Auto-fill based on selected preset
                if selected_preset != "Custom":
                    # Preset selected
                    preset_config = get_preset(selected_preset)
                    
                    # If user switched to a different preset (not current one), clear API key
                    # If it's the same as current config, keep API key
                    if selected_preset == current_preset:
                        # Same preset as saved config: keep API key
                        default_api_key = current_llm["api_key"]
                    else:
                        # Different preset: use default_api_key if provided (e.g., Ollama), otherwise clear
                        default_api_key = preset_config.get("default_api_key", "")
                    
                    default_base_url = preset_config.get("base_url", "")
                    default_model = preset_config.get("model", "")
                    
                    # Show API key URL if available
                    if preset_config.get("api_key_url"):
                        st.markdown(f"🔑 [{tr('settings.llm.get_api_key')}]({preset_config['api_key_url']})")
                else:
                    # Custom: show current saved config (if any)
                    default_api_key = current_llm["api_key"]
                    default_base_url = current_llm["base_url"]
                    default_model = current_llm["model"]
                
                st.markdown("---")
                
                # API Key (use unique key to force refresh when switching preset)
                llm_api_key = st.text_input(
                    f"{tr('settings.llm.api_key')} *",
                    value=default_api_key,
                    type="password",
                    help=tr("settings.llm.api_key_help"),
                    key=f"llm_api_key_input_{selected_preset}"
                )
                
                # Base URL (use unique key based on preset to force refresh)
                llm_base_url = st.text_input(
                    f"{tr('settings.llm.base_url')} *",
                    value=default_base_url,
                    help=tr("settings.llm.base_url_help"),
                    key=f"llm_base_url_input_{selected_preset}"
                )
                
                # Model selection with dropdown and load button
                # Initialize session state for loaded models
                if "llm_loaded_models" not in st.session_state:
                    st.session_state.llm_loaded_models = []
                
                # Build model options: Custom option + loaded models
                CUSTOM_MODEL_OPTION = f"✏️ {tr('settings.llm.custom_model')}"
                model_options = [CUSTOM_MODEL_OPTION] + st.session_state.llm_loaded_models
                
                # Determine default selection
                if default_model in st.session_state.llm_loaded_models:
                    default_model_index = model_options.index(default_model)
                else:
                    # Default model not in loaded list, use custom
                    default_model_index = 0
                
                # Model dropdown with load button on the right
                model_col, load_col, test_col = st.columns([3, 1, 1])
                
                with model_col:
                    selected_model_option = st.selectbox(
                        f"{tr('settings.llm.model')} *",
                        options=model_options,
                        index=default_model_index,
                        help=tr("settings.llm.model_help"),
                        key=f"llm_model_select_{selected_preset}"
                    )
                
                with load_col:
                    st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
                    load_clicked = st.button(
                        f"🔄 {tr('settings.llm.load_models')}",
                        help=tr("settings.llm.load_models_help"),
                        key="load_models_btn",
                        use_container_width=True
                    )
                
                with test_col:
                    st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
                    test_clicked = st.button(
                        f"🔌 {tr('settings.llm.test_connection')}",
                        help=tr("settings.llm.test_connection_help"),
                        key="test_llm_connection_btn",
                        use_container_width=True
                    )
                
                # Handle load models button click
                if load_clicked:
                    if llm_api_key and llm_base_url:
                        try:
                            from pixelle_video.utils.llm_util import fetch_available_models
                            with st.spinner(tr("settings.llm.loading_models")):
                                models = fetch_available_models(llm_api_key, llm_base_url)
                                st.session_state.llm_loaded_models = models
                                st.success(tr("settings.llm.models_loaded").replace("{count}", str(len(models))))
                                safe_rerun()
                        except Exception as e:
                            st.error(tr("settings.llm.models_load_failed").replace("{error}", str(e)))
                    else:
                        st.warning(tr("status.llm_config_incomplete"))
                
                # Handle test connection button click
                if test_clicked:
                    if llm_api_key and llm_base_url:
                        try:
                            from pixelle_video.utils.llm_util import test_llm_connection
                            with st.spinner(tr("settings.llm.loading_models")):
                                success, message, model_count = test_llm_connection(llm_api_key, llm_base_url)
                                if success:
                                    st.success(tr("settings.llm.connection_success").replace("{count}", str(model_count)))
                                else:
                                    st.error(tr("settings.llm.connection_failed").replace("{error}", message))
                        except Exception as e:
                            st.error(tr("settings.llm.connection_failed").replace("{error}", str(e)))
                    else:
                        st.warning(tr("status.llm_config_incomplete"))
                
                # If custom option selected, show text input for custom model name
                if selected_model_option == CUSTOM_MODEL_OPTION:
                    llm_model = st.text_input(
                        tr("settings.llm.custom_model_input"),
                        value=default_model,
                        help=tr("settings.llm.model_help"),
                        key=f"llm_custom_model_input_{selected_preset}"
                    )
                else:
                    llm_model = selected_model_option
        
        # ====================================================================
        # Column 2: Custom API Media Model Settings
        # ====================================================================
        zh = get_language() == "zh_CN"
        api_cfg = config_manager.get_api_providers_config()
        common_cfg = api_cfg.get("common", {})
        custom_cfg = api_cfg.get("custom", {})

        with custom_media_col:
            with st.container(border=True):
                st.markdown(
                    "**🔀 API 媒体模型（第三方中转）**" if zh
                    else "**🔀 API Media Models (Relay)**"
                )
                st.caption(
                    "用于通过第三方中转服务（如 new-api）调用图像/视频生成模型。"
                    "配置中转地址和 API Key 后，在媒体生成中选择 api/custom/ 开头的模型即可。"
                    if zh
                    else "For image/video generation via third-party relay services (e.g. new-api). "
                    "Configure the relay base URL and API key, then select api/custom/ models in the media workflow."
                )

                api_print_model_input = st.checkbox(
                    "打印模型请求参数" if zh else "Print model request parameters",
                    value=bool(common_cfg.get("print_model_input", False)),
                    help=(
                        "调试用。开启后会在终端打印发送给图像/视频模型的 prompt、模型名和输入文件路径。"
                        if zh
                        else "For debugging. Prints prompts, model names and input file paths sent to image/video models."
                    ),
                    key="api_media_print_model_input",
                )

                st.markdown("---")

                c_key_col, c_url_col = st.columns(2)
                with c_key_col:
                    api_custom_key = st.text_input(
                        "API Key *",
                        value=custom_cfg.get("api_key", ""),
                        type="password",
                        key="api_media_custom_key",
                    )
                with c_url_col:
                    api_custom_base_url = st.text_input(
                        "Base URL *",
                        value=custom_cfg.get("base_url", ""),
                        placeholder="http://localhost:3000/v1",
                        key="api_media_custom_base_url",
                    )

                st.markdown(
                    "**模型列表**（逗号分隔，填写你在中转服务中可用的模型名）" if zh
                    else "**Model List** (comma-separated, enter model names available in your relay service)"
                )
                api_custom_video_models = st.text_input(
                    "视频模型名" if zh else "Video model names",
                    value=custom_cfg.get("video_models", ""),
                    placeholder="sora-1, doubao-seedance-2-0-260128",
                    help=(
                        "填写中转服务支持的视频生成模型名，多个用英文逗号分隔。"
                        if zh
                        else "Enter video model names available in your relay service, comma-separated."
                    ),
                    key="api_media_custom_video_models",
                )
                api_custom_image_models = st.text_input(
                    "图片模型名" if zh else "Image model names",
                    value=custom_cfg.get("image_models", ""),
                    placeholder="gpt-image-1, flux-1",
                    help=(
                        "填写中转服务支持的图像生成模型名，多个用英文逗号分隔。"
                        if zh
                        else "Enter image model names available in your relay service, comma-separated."
                    ),
                    key="api_media_custom_image_models",
                )
        
        # ====================================================================
        # Action Buttons (full width at bottom)
        # ====================================================================
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(tr("btn.save_config"), use_container_width=True, key="save_config_btn"):
                try:
                    # Validate and save LLM configuration
                    if not (llm_api_key and llm_base_url and llm_model):
                        st.error(tr("status.llm_config_incomplete"))
                    else:
                        config_manager.set_llm_config(llm_api_key, llm_base_url, llm_model)

                    # Save API media provider configuration.
                    config_manager.set_api_provider_config("common", {
                        "print_model_input": bool(api_print_model_input),
                    })

                    # Validate custom API media model configuration (required)
                    custom_errors = []
                    if not api_custom_key:
                        custom_errors.append("API Key" if not zh else "API Key")
                    if not api_custom_base_url:
                        custom_errors.append("Base URL" if not zh else "Base URL")
                    if not api_custom_video_models and not api_custom_image_models:
                        custom_errors.append(
                            "视频模型名或图片模型名（至少填一项）" if zh
                            else "Video model names or Image model names (at least one)"
                        )
                    if custom_errors:
                        st.error(
                            f"API 媒体模型配置不完整，请填写：{', '.join(custom_errors)}" if zh
                            else f"API media model configuration incomplete, please fill: {', '.join(custom_errors)}"
                        )
                    else:
                        config_manager.set_api_provider_config("custom", {
                            "api_key": api_custom_key or "",
                            "base_url": api_custom_base_url or "",
                            "video_models": api_custom_video_models or "",
                            "image_models": api_custom_image_models or "",
                        })
                    
                    # Only save to file if LLM and custom config are valid
                    if llm_api_key and llm_base_url and llm_model and not custom_errors:
                        config_manager.save()
                        st.success(tr("status.config_saved"))
                        safe_rerun()
                except Exception as e:
                    st.error(f"{tr('status.save_failed')}: {str(e)}")
        
        with col2:
            if st.button(tr("btn.reset_config"), use_container_width=True, key="reset_config_btn"):
                # Reset to default
                from pixelle_video.config.schema import PixelleVideoConfig
                config_manager.config = PixelleVideoConfig()
                config_manager.save()
                st.success(tr("status.config_reset"))
                safe_rerun()
